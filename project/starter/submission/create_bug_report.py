import json
import os
import uuid
from datetime import datetime, timezone

import boto3

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
REQUIRED_FIELDS = ("description", "stepsToReproduce", "environment")


def lambda_handler(event, context):
    print("EVENT:", json.dumps(event, default=str))
    print(
        "CONTEXT:",
        json.dumps(
            {
                "tool": getattr(context, "bedrockAgentCoreToolName", None),
                "gateway": getattr(context, "bedrockAgentCoreGatewayId", None),
                "target": getattr(context, "bedrockAgentCoreTargetId", None),
            },
            default=str,
        ),
    )

    body = event if isinstance(event, dict) else {}

    description = str(body.get("description") or "").strip()
    steps = str(body.get("stepsToReproduce") or "").strip()
    environment = str(body.get("environment") or "").strip()

    missing = [
        field
        for field, value in {
            "description": description,
            "stepsToReproduce": steps,
            "environment": environment,
        }.items()
        if not value
    ]
    if missing:
        return {
            "error": "missing_required_fields",
            "fields": missing,
        }

    ticket_id = str(uuid.uuid4())
    item = {
        "ticketId": ticket_id,
        "description": description,
        "stepsToReproduce": steps,
        "environment": environment,
        "status": "OPEN",
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }

    table.put_item(Item=item)

    return {
        "ticketId": ticket_id,
        "status": "OPEN",
    }
