import json
import time
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from app.config import RETELL_API_KEY, VERIFY_RETELL_WEBHOOKS
from app.database import get_database
from app.services.retell_service import retell_client

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
STORED_EVENTS = {
    "call_started",
    "transcript_updated",
    "call_ended",
    "call_analyzed",
}


@router.post("/retell")
async def retell_webhook(
    request: Request,
) -> dict[str, str]:
    """Verify, acknowledge, and persist Retell call events."""
    body = await request.body()
    signature = request.headers.get("x-retell-signature", "")
    if VERIFY_RETELL_WEBHOOKS and (
        not RETELL_API_KEY
        or not signature
        or not retell_client.verify(body.decode(), RETELL_API_KEY, signature)
    ):
        raise HTTPException(status_code=401, detail="Invalid Retell signature")

    try:
        payload = json.loads(body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Malformed webhook payload") from exc

    event = payload.get("event", "")
    call = payload.get("call") or {}
    call_id = call.get("call_id") or payload.get("call_id", "")

    if not call_id:
        raise HTTPException(
            status_code=400,
            detail="Missing call_id in webhook payload",
        )

    if event in STORED_EVENTS:
        call["call_id"] = call_id
        await process_call_event(event, call)

    return {"status": "acknowledged", "event": event, "call_id": call_id}


def call_document(event: str, call: dict[str, Any]) -> dict[str, Any]:
    """Map a Retell call payload to the persisted call shape."""
    variables = call.get("retell_llm_dynamic_variables") or {}
    metadata = call.get("metadata") or {}
    analysis = call.get("call_analysis") or {}
    start_timestamp = call.get("start_timestamp")
    end_timestamp = call.get("end_timestamp")
    duration_ms = call.get("duration_ms")
    if duration_ms is None and start_timestamp and end_timestamp:
        duration_ms = end_timestamp - start_timestamp

    document = {
        "retell_call_id": call["call_id"],
        "profile_id": metadata.get("profile_id"),
        "agent_id": call.get("agent_id", ""),
        "customer_name": variables.get("customer_name", ""),
        "call_status": call.get("call_status", ""),
        "call_type": call.get("call_type", ""),
        "start_timestamp": start_timestamp,
        "end_timestamp": end_timestamp,
        "duration_ms": duration_ms,
        "recording_url": call.get("recording_url"),
        "transcript": call.get("transcript"),
        "transcript_object": call.get("transcript_object"),
        "transcript_with_tool_calls": call.get("transcript_with_tool_calls"),
        "call_summary": analysis.get("call_summary"),
        "call_successful": analysis.get("call_successful"),
        "user_sentiment": analysis.get("user_sentiment"),
        "qualification": analysis.get("custom_analysis_data") or {},
        "disconnection_reason": call.get("disconnection_reason"),
        "last_event": event,
        "updated_at": time.time(),
    }
    return {key: value for key, value in document.items() if value is not None}


async def process_call_event(event: str, call: dict[str, Any]) -> None:
    """Idempotently persist the latest state of a Retell call."""
    document = call_document(event, call)
    database = await get_database()
    await database["calls"].update_one(
        {"retell_call_id": call["call_id"]},
        {
            "$set": document,
            "$setOnInsert": {"created_at": time.time()},
        },
        upsert=True,
    )
