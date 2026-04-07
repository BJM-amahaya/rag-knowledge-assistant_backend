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