"""The explanation layer: turns the deterministic risk numbers (risk.py,
corridor.py) into plain-language guidance via Amazon Bedrock.

As with the rules-engine-vs-LLM split in the previous hackathon project: the
AI never computes the risk numbers themselves, only explains and prioritises
what the deterministic engine already calculated. See DECISIONS.md #7.

Bedrock requires AWS credentials and model access, neither of which exist in
every environment (a laptop with no AWS account, this sandbox, CI). Rather
than fail the whole demo, build_explanation() falls back to a deterministic
template -- see DECISIONS.md #11.
"""
from __future__ import annotations

import json
import os
from typing import Any

BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")

SYSTEM_PROMPT = """You are Kavach, a safety copilot for outdoor workers in Delhi. \
You are given deterministic risk numbers (pollution dose, heat index, route \
scores) that you must NOT recalculate or contradict -- only explain them \
plainly, in one or two short sentences, and say what the person should do \
next. Keep it concrete and calm, never alarmist. If take_cover is true, say \
so clearly and name the nearest safe option if one is given."""


def _invoke_bedrock(prompt: str) -> str | None:
    try:
        import boto3

        client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
        body = {
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "system": [{"text": SYSTEM_PROMPT}],
            "inferenceConfig": {"maxTokens": 200, "temperature": 0.2},
        }
        resp = client.converse(
            modelId=BEDROCK_MODEL_ID,
            messages=body["messages"],
            system=body["system"],
            inferenceConfig=body["inferenceConfig"],
        )
        return resp["output"]["message"]["content"][0]["text"].strip()
    except Exception:
        return None


def _fallback_explanation(context: dict[str, Any]) -> str:
    """A deterministic, template-based explanation used when Bedrock is not
    reachable (no credentials, no model access, offline demo). Still reads
    every number from `context`, it just doesn't phrase it with an LLM.
    """
    persona = context.get("persona_name", "This worker")
    dose = context.get("dose", {})
    heat = context.get("heat", {})
    parts = []

    cig = dose.get("cigarette_equivalent")
    if cig is not None:
        parts.append(f"{persona} has inhaled roughly {cig} cigarette-equivalents of pollution so far today.")

    if heat.get("take_cover"):
        parts.append(
            f"Heat risk is '{heat.get('risk')}' (effective heat index ~{heat.get('heat_index_celsius')}C) "
            "-- take cover in shade now."
        )
    elif heat:
        parts.append(f"Heat risk is currently '{heat.get('risk', 'safe')}'.")

    route = context.get("route_recommendation")
    if route:
        parts.append(f"For the next trip, {route}.")

    return " ".join(parts) if parts else "No elevated risk right now."


def build_explanation(context: dict[str, Any]) -> dict[str, Any]:
    """context should contain persona_name, dose (DoseResult-like dict),
    heat (HeatResult-like dict), and optionally route_recommendation (str).
    Returns {"text": str, "source": "bedrock" | "fallback"}.
    """
    prompt = (
        "Risk context (JSON): "
        + json.dumps(context, default=str)
        + "\n\nExplain this to the worker/dispatcher in 1-2 sentences and say what to do next."
    )
    bedrock_text = _invoke_bedrock(prompt)
    if bedrock_text:
        return {"text": bedrock_text, "source": "bedrock"}
    return {"text": _fallback_explanation(context), "source": "fallback"}
