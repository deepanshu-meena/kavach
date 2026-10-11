"""AWS Lambda entrypoints.

api_handler: wraps the FastAPI app (api.py) with Mangum so API Gateway can
call the exact same routes the local uvicorn server serves -- one set of
route definitions, not a duplicated hand-rolled router (see DECISIONS.md #12).

ingest_handler: meant to run on an EventBridge schedule (see template.yaml).
Pulls fresh readings for each known locality and, if a DynamoDB table is
configured, writes them there for the frontend/agent to read later. Falls
back to a no-op log line if boto3/DynamoDB isn't available, so this is safe
to invoke locally too.
"""
from __future__ import annotations

import json
import os
import time
from typing import Any

from mangum import Mangum

from . import data_sources
from .api import app

api_handler = Mangum(app)

DYNAMODB_TABLE = os.getenv("KAVACH_TABLE_NAME", "")


def ingest_handler(event: dict[str, Any] | None = None, _context: Any = None) -> dict[str, Any]:
    results = []
    for locality, (lat, lon) in data_sources.LOCALITY_COORDS.items():
        snapshot = data_sources.get_locality_snapshot(locality, lat, lon)
        snapshot["fetched_at"] = int(time.time())
        results.append(snapshot)

        if DYNAMODB_TABLE:
            try:
                import boto3

                table = boto3.resource("dynamodb").Table(DYNAMODB_TABLE)
                table.put_item(
                    Item={
                        "pk": f"locality#{locality}",
                        "sk": str(snapshot["fetched_at"]),
                        **{k: str(v) for k, v in snapshot.items() if k != "fire_signal"},
                    }
                )
            except Exception as exc:  # pragma: no cover - requires live AWS
                print(f"DynamoDB write skipped for {locality}: {exc}")

    return {"statusCode": 200, "body": json.dumps({"ingested": len(results)})}
