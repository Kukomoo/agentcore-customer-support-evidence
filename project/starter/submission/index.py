import html
import json
import os
import re
import uuid
from datetime import datetime, timezone

import boto3

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])

ZERO_WIDTH = re.compile(r"[\u200b\u200c\u200d\ufeff]")
PLACEHOLDERS = {
    "",
    "n/a",
    "missing",
    "na",
    "none",
    "null",
    "unknown",
    "not provided",
    "not applicable",
}


def clean(value):
    text = html.unescape(str(value or ""))
    text = ZERO_WIDTH.sub("", text)
    return " ".join(text.split()).strip()


def is_missing(value):
    normalized = clean(value).lower()
    return not normalized or normalized in PLACEHOLDERS


def lambda_handler(event, context):
    print("EVENT:", json.dumps(event, default=str))

    body = event if isinstance(event, dict) else {}

    raw = {
        "description": body.get("description"),
        "stepsToReproduce": body.get("stepsToReproduce"),
        "environment": body.get("environment"),
    }

    missing = [field for field, value in raw.items() if is_missing(value)]

    if missing:
        return {
            "error": "missing_required_fields",
            "fields": missing,
            "message": (
                "Do not create a ticket until description, stepsToReproduce, "
                "and environment contain real customer-provided values."
            ),
        }

    ticket_id = str(uuid.uuid4())

    table.put_item(
        Item={
            "ticketId": ticket_id,
            "description": clean(raw["description"]),
            "stepsToReproduce": clean(raw["stepsToReproduce"]),
            "environment": clean(raw["environment"]),
            "status": "OPEN",
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }
    )

    return {
        "ticketId": ticket_id,
        "status": "OPEN",
    }
