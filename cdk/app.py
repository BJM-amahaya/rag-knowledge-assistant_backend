#!/usr/bin/env python3
import aws_cdk as cdk
from cdk_stack import RagKnowledgeAssistantStack

app = cdk.App()

RagKnowledgeAssistantStack(
    app,
    "amahaya-rag",
    env=cdk.Environment(
        region="ap-northeast-1"
        )
)


app.synth()