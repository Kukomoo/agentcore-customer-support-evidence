import json
import uuid

import boto3

REGION = "us-east-1"
HARNESS_ARN = (
    "arn:aws:bedrock-agentcore:us-east-1:972881187492:"
    "harness/bug_report_support_harness-ZCQs4I4T3P"
)
RUNTIME_SESSION_ID = f"bug-report-demo-{uuid.uuid4()}"

runtime = boto3.client("bedrock-agentcore", region_name=REGION)

turns = [
    (
        "I need to report a bug. The checkout page crashes when I try to pay. "
        "Please ask me for any missing details before filing a report."
    ),
    (
        "To reproduce it: add an item to the cart, enter card details, "
        "and click Place order. The page crashes."
    ),
    "My environment is Chrome 126 on Windows 11 on a laptop.",
]

def invoke(message):
    print(f"\nCustomer: {message}")
    print("Assistant: ", end="", flush=True)

    response = runtime.invoke_harness(
        harnessArn=HARNESS_ARN,
        runtimeSessionId=RUNTIME_SESSION_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": message}],
            }
        ],
    )

    tool_name = None
    tool_input = ""

    for event in response["stream"]:
        if "contentBlockStart" in event:
            start = event["contentBlockStart"].get("start", {})
            tool_use = start.get("toolUse")
            if tool_use:
                tool_name = tool_use.get("name", "unknown_tool")
                print(f"\n[tool call] {tool_name}", end="", flush=True)

        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})

            if "text" in delta:
                print(delta["text"], end="", flush=True)

            if "toolUse" in delta:
                tool_input += delta["toolUse"].get("input", "")

            if "toolResult" in delta:
                for result in delta["toolResult"]:
                    if "json" in result:
                        print(
                            "\n[tool result] "
                            + json.dumps(result["json"], default=str),
                            end="",
                            flush=True,
                        )
                    elif "text" in result:
                        print(
                            f"\n[tool result] {result['text']}",
                            end="",
                            flush=True,
                        )

        if "messageStop" in event:
            reason = event["messageStop"].get("stopReason")
            if reason:
                print(f"\n[stop reason] {reason}", end="", flush=True)

    if tool_name and tool_input:
        print(f"\n[tool input] {tool_input}", end="", flush=True)

    print()

for turn in turns:
    invoke(turn)
