import json
from pathlib import Path

import boto3

REGION = "us-east-1"
HARNESS_ID = "bug_report_support_harness-ZCQs4I4T3P"

root = Path(__file__).resolve().parent
prompt = (root / "system_prompt.txt").read_text(encoding="utf-8")
faq = (root / "online_shop_faq.md").read_text(encoding="utf-8")
system_prompt = prompt.replace("{{FAQ}}", faq)

client = boto3.client("bedrock-agentcore-control", region_name=REGION)

response = client.update_harness(
    harnessId=HARNESS_ID,
    systemPrompt=[{"text": system_prompt}],
)

print(json.dumps(response, indent=2, default=str))
