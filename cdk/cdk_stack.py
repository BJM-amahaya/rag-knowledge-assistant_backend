from aws_cdk import (
    Stack, Duration, RemovalPolicy, CfnOutput,
    aws_cognito as cognito,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_s3 as s3,
    aws_ssm as ssm,
)
from constructs import Construct

class RagKnowledgeAssistantStack(Stack):
    def __init__(self,scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        bedrock_kb_id = self.node.try_get_context("bedrock_kb_id") or ""
        bedrock_datasource_id = self.node.try_get_context("bedrock_datasource_id") or ""
        bedrock_model_id = self.node.try_get_context("bedrock_model_id") or "anthropic.claude-sonnet-4-20250514"
        s3_bucket_name = self.node.try_get_context("s3_documents_bucket_name") or "rag-app-documents"
        amplify_domain = self.node.try_get_context("amplify_domain") or ""

        # ---- Cognito ----
        user_pool = cognito.UserPool(
            self,
            "UserPool",
            user_pool_name="rag-user-pool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            removal_policy=RemovalPolicy.DESTROY,
        )

        user_pool_client = cognito.UserPoolClient(
            self,
            "UserPoolClient",
            user_pool=user_pool,
            user_pool_client_name="rag-web-client",
            auth_flows=cognito.AuthFlow(
                user_password=True,
                user_srp=True,
            ),
        )

        # ---- S3 ----
        documents_bucket = s3.Bucket(
            self,
            "DocumentsBucket",
            bucket_name=s3_bucket_name,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            cors=[s3.CorsRule(
                allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.PUT],
                allowed_origins=["*"],
                allowed_headers=["*"],
            )],
        )

        # ---- DynamoDB ----
        documents_table = dynamodb.Table(
            self,
            "DocumentsTable",
            table_name="rag-documents",
            partition_key=dynamodb.Attribute(
                name="docId", type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        tasks_table = dynamodb.Table(
            self,
            "TasksTable",
            table_name="rag-tasks",
            partition_key=dynamodb.Attribute(
                name="taskId", type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        connections_table = dynamodb.Table(
            self,
            "ConnectionsTable",
            table_name="rag-ws-connections",
            partition_key=dynamodb.Attribute(
                name="connectionId", type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        # ---- Lambda (REST API) ----
        rest_lambda = _lambda.Function(
            self,
            "RestApiLambda",
            function_name="rag-rest-api",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="lambda_handler.handler",
            code=_lambda.Code.from_asset(
                "..",
                exclude=["cdk", "cdk.out", ".venv", "__pycache__", "*.pyc", ".git"],
            ),
            timeout=Duration.seconds(60),
            memory_size=512,
            environment={
                "AWS_REGION_NAME": "ap-northeast-1",
                "BEDROCK_KB_ID": bedrock_kb_id,
                "BEDROCK_DATA_SOURCE_ID": bedrock_datasource_id,
                "BEDROCK_MODEL_ID": bedrock_model_id,
                "S3_DOCUMENTS_BUCKET": s3_bucket_name,
                "DYNAMODB_DOCUMENTS_TABLE": documents_table.table_name,
                "DYNAMODB_TASKS_TABLE": tasks_table.table_name,
                "DYNAMODB_CONNECTIONS_TABLE": connections_table.table_name,
                "CORS_ALLOWED_ORIGIN": f"https://{amplify_domain}" if amplify_domain else "http://localhost:3000",
            },
        )

        # ---- IAM ポリシー ----
        documents_table.grant_read_write_data(rest_lambda)
        tasks_table.grant_read_write_data(rest_lambda)
        connections_table.grant_read_write_data(rest_lambda)

        documents_bucket.grant_read_write(rest_lambda)

        rest_lambda.add_to_role_policy(iam.PolicyStatement(
            actions=[
                "bedrock:InvokeModel",
                "bedrock:Retrieve",
                "bedrock:StartIngestionJob",
            ],
            resources=["*"],
        ))

        # ---- API Gateway ----
        cognito_authorizer = apigw.CognitoUserPoolsAuthorizer(
            self,
            "CognitoAuthorizer",
            cognito_user_pools=[user_pool],
        )

        rest_api = apigw.LambdaRestApi(
            self,
            "RestApi",
            handler=rest_lambda,
            rest_api_name="rag-rest-api",
            proxy=True,
            default_method_options=apigw.MethodOptions(
                authorizer=cognito_authorizer,
                authorization_type=apigw.AuthorizationType.COGNITO,
            ),
        )

        # ヘルスチェック用（認証不要）
        root_resource = rest_api.root
        root_resource.add_method(
            "GET",
            apigw.LambdaIntegration(rest_lambda),
            authorization_type=apigw.AuthorizationType.NONE,
        )

        # ---- SSM パラメータストア ----
        ssm.StringParameter(
            self,
            "ApiUrlParam",
            parameter_name="/rag-app/api-url",
            string_value=rest_api.url,
        )

        ssm.StringParameter(
            self,
            "UserPoolIdParam",
            parameter_name="/rag-app/user-pool-id",
            string_value=user_pool.user_pool_id,
        )

        ssm.StringParameter(
            self,
            "UserPoolClientIdParam",
            parameter_name="/rag-app/user-pool-client-id",
            string_value=user_pool_client.user_pool_client_id,
        )

        # ---- 出力 ----
        CfnOutput(self, "ApiUrl", value=rest_api.url)
        CfnOutput(self, "UserPoolId", value=user_pool.user_pool_id)
        CfnOutput(self, "UserPoolClientId", value=user_pool_client.user_pool_client_id)