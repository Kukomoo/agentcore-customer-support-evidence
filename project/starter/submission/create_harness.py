import json
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
HARNESS_NAME = "bug_report_support_harness"
MODEL_ID = "amazon.nova-pro-v1:0"
HARNESS_ROLE_ARN = (
    "arn:aws:iam::972881187492:role/bug-report-agentcore-harness-role"
)
GATEWAY_ARN = (
    "arn:aws:bedrock-agentcore:us-east-1:972881187492:"
    "gateway/bug-report-gateway-ctgh2lwsmp"
)

root = Path(__file__).resolve().parent
prompt = (root / "system_prompt.txt").read_text(encoding="utf-8")
faq = (root / "online_shop_faq.md").read_text(encoding="utf-8")
system_prompt = prompt.replace("{{FAQ}}", faq)

client = boto3.client("bedrock-agentcore-control", region_name=REGION)

request = {
    "harnessName": HARNESS_NAME,
    "executionRoleArn": HARNESS_ROLE_ARN,
    "model": {
        "bedrockModelConfig": {
            "modelId": MODEL_ID,
            "maxTokens": 1024,
            "temperature": 0.0,
        }
    },
    "systemPrompt": [{"text": system_prompt}],
    "tools": [
        {
            "type": "agentcore_gateway",
            "name": "bugreports",
            "config": {
                "agentCoreGateway": {
                    "gatewayArn": GATEWAY_ARN,
                    "outboundAuth": {"awsIam": {}},
                }
            },
        }
    ],
    "maxIterations": 8,
    "maxTokens": 1024,
    "timeoutSeconds": 300,
    "tags": {
        "Project": "customer-support-bug-report",
    },
}

try:
    response = client.create_harness(**request)
except ClientError as exc:
    print(json.dumps(exc.response, indent=2, default=str))
    raise
else:
    print("Harness created:")
    print(json.dumps(response, indent=2, default=str))
