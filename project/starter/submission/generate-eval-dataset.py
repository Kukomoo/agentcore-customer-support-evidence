#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

import boto3


def invoke_flow_once(
    client,
    flow_identifier: str,
    flow_alias_identifier: str,
    input_node_name: str,
    prompt: str,
    enable_trace: bool = False,
) -> Dict[str, Any]:
    """Invoke a Bedrock Flow once and return its final output text."""
    resp = client.invoke_flow(
        flowIdentifier=flow_identifier,
        flowAliasIdentifier=flow_alias_identifier,
        enableTrace=enable_trace,
        inputs=[
            {
                "nodeName": input_node_name,
                "nodeOutputName": "document",
                "content": {"document": prompt},
            }
        ],
    )

    last_text_any = None

    for event in resp["responseStream"]:
        print("EVENT: " + str(event))

        if "flowOutputEvent" in event:
            output = event["flowOutputEvent"].get("content", {}).get("document")
            if output is not None:
                last_text_any = output

        elif "flowMultiTurnInputRequestEvent" in event:
            output = event["flowMultiTurnInputRequestEvent"].get("content", {}).get("document")
            if output is not None:
                last_text_any = output

    return {
        "final_output_text": last_text_any,
    }


def main():
    p = argparse.ArgumentParser(
        description="Run Bedrock Flow tests and emit Bedrock Evaluations JSONL."
    )
    p.add_argument(
        "--tests-json",
        required=True,
        help="Path to the test suite JSON.",
    )
    p.add_argument(
        "--flow-id",
        required=True,
        help="Bedrock Flow identifier.",
    )
    p.add_argument(
        "--flow-alias-id",
        required=True,
        help="Bedrock Flow alias identifier.",
    )
    p.add_argument(
        "--model-identifier",
        default="my-flow-app",
        help="Value for modelResponses[0].modelIdentifier.",
    )
    p.add_argument(
        "--out-jsonl",
        default="output_eval_dataset.jsonl",
        help="Where to write the evaluation dataset JSONL.",
    )
    p.add_argument(
        "--region",
        default=None,
        help="AWS Region; otherwise uses the default Boto configuration.",
    )
    p.add_argument(
        "--enable-trace",
        action="store_true",
        help="Enable Bedrock Flow trace events.",
    )
    args = p.parse_args()

    suite = json.loads(Path(args.tests_json).read_text(encoding="utf-8"))
    input_node_name = suite["flowInputNode"]["nodeName"]
    tests = suite["tests"]

    print("Input node name: " + input_node_name)

    session = (
        boto3.Session(region_name=args.region)
        if args.region
        else boto3.Session()
    )
    client = session.client("bedrock-agent-runtime")

    out_path = Path(args.out_jsonl)
    n_ok = 0

    with out_path.open("w", encoding="utf-8") as f:
        for t in tests:
            test_id = t["id"]
            reference = t.get("expected", "")
            prompt = t.get("prompt", "")

            try:
                result = invoke_flow_once(
                    client=client,
                    flow_identifier=args.flow_id,
                    flow_alias_identifier=args.flow_alias_id,
                    input_node_name=input_node_name,
                    prompt=prompt,
                    enable_trace=args.enable_trace,
                )
                response_text = result["final_output_text"]
                n_ok += 1

                if response_text is None:
                    response_text = "[FLOW_ERROR] No flow output event was returned."

            except Exception as e:
                print(e, file=sys.stderr)
                response_text = f"[FLOW_ERROR] {type(e).__name__}: {e}"

            record = {
                "prompt": prompt,
                "referenceResponse": reference,
                "modelResponses": [
                    {
                        "response": response_text,
                        "modelIdentifier": args.model_identifier,
                    }
                ],
            }

            f.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(f"{test_id}: wrote eval line", file=sys.stderr)

    print(
        f"\nWrote {len(tests)} JSONL lines to {out_path} "
        f"({n_ok} flow calls succeeded).",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
