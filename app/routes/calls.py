from fastapi import APIRouter, Depends, HTTPException, status
import logging
from retell import APIStatusError
from starlette.concurrency import run_in_threadpool

from app.database import get_database
from app.routes.profiles import profile_object_id
from app.schemas.call import CallStartRequest, CallStartResponse, CallHistoryQuery, CallItemResponse, CallHistoryResponse, CallResponse
from app.services.retell_service import create_web_call

router = APIRouter(prefix="/api/calls", tags=["calls"])
logger = logging.getLogger(__name__)


@router.post("/start", response_model=CallStartResponse)
async def start_call(
    request: CallStartRequest,
) -> CallStartResponse:
    """Start a new Retell browser voice call."""
    database = await get_database()
    profile = await database["profiles"].find_one(
        {"_id": profile_object_id(request.profile_id)}
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    try:
        call_id_access_token = await run_in_threadpool(
            create_web_call,
            customer_name=profile["customer_name"],
            language_to_speak=profile["language_to_speak"],
            agent_name=request.agent_name,
            profile_id=request.profile_id,
            dynamic_variables=profile.get("dynamic_variables"),
            metadata=profile.get("metadata"),
        )
    except APIStatusError as exc:
        logger.warning("Retell rejected call creation: %s", exc)
        raise HTTPException(
            status_code=exc.status_code,
            detail="Retell rejected call creation",
        ) from exc
    except Exception as exc:
        logger.exception("Retell API error starting call")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create Retell call",
        ) from exc

    await database["calls"].update_one(
        {"retell_call_id": call_id_access_token["call_id"]},
        {
            "$set": {
                "profile_id": request.profile_id,
                "agent_id": "",
                "customer_name": profile["customer_name"],
                "call_status": "registered",
                "call_type": "web_call",
                "updated_at": __import__("time").time(),
            },
            "$setOnInsert": {"created_at": __import__("time").time()},
        },
        upsert=True,
    )
    return CallStartResponse(
        call_id=call_id_access_token["call_id"],
        access_token=call_id_access_token["access_token"],
        transport=call_id_access_token.get("transport"),
        ice_servers=call_id_access_token.get("ice_servers"),
    )


@router.get("", response_model=CallHistoryResponse)
async def get_calls(
    query: CallHistoryQuery = Depends(),
) -> CallHistoryResponse:
    """Get recent calls from MongoDB with pagination and optional filtering."""
    filters = {}
    if query.outcome:
        filters["qualification.call_outcome"] = query.outcome
    if query.profile_id:
        filters["profile_id"] = query.profile_id

    database = await get_database()
    calls = database["calls"]
    documents = await calls.find(filters).sort("created_at", -1).skip(
        (query.page - 1) * query.limit
    ).limit(query.limit).to_list(length=query.limit)
    return CallHistoryResponse(
        items=[CallItemResponse(**document) for document in documents],
        page=query.page,
        limit=query.limit,
        total=await calls.count_documents(filters),
    )


@router.get("/{retell_call_id}", response_model=CallResponse)
async def get_call(
    retell_call_id: str,
) -> CallResponse:
    """Get a single call record by retell_call_id."""
    database = await get_database()
    document = await database["calls"].find_one(
        {"retell_call_id": retell_call_id}
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found",
        )
    document["id"] = str(document.pop("_id"))
    return CallResponse(**document)
