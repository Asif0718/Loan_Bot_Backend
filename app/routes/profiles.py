import time

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_database
from app.schemas.call import CallHistoryQuery, CallHistoryResponse, CallItemResponse
from app.schemas.profile import ProfileCreate, ProfileListResponse, ProfileResponse

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


def serialize_profile(document: dict) -> ProfileResponse:
    return ProfileResponse(id=str(document.pop("_id")), **document)


def profile_object_id(profile_id: str) -> ObjectId:
    if not ObjectId.is_valid(profile_id):
        raise HTTPException(status_code=404, detail="Profile not found")
    return ObjectId(profile_id)


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(profile: ProfileCreate) -> ProfileResponse:
    database = await get_database()
    now = time.time()
    document = profile.model_dump() | {"created_at": now, "updated_at": now}
    result = await database["profiles"].insert_one(document)
    return ProfileResponse(id=str(result.inserted_id), **document)


@router.get("", response_model=ProfileListResponse)
async def get_profiles(
    page: int = 1,
    limit: int = 20,
) -> ProfileListResponse:
    if page < 1 or limit < 1 or limit > 100:
        raise HTTPException(status_code=422, detail="Invalid pagination")

    database = await get_database()
    profiles = database["profiles"]
    documents = await profiles.find().sort("created_at", -1).skip(
        (page - 1) * limit
    ).limit(limit).to_list(length=limit)
    return ProfileListResponse(
        items=[serialize_profile(document) for document in documents],
        page=page,
        limit=limit,
        total=await profiles.count_documents({}),
    )


@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(profile_id: str) -> ProfileResponse:
    database = await get_database()
    document = await database["profiles"].find_one(
        {"_id": profile_object_id(profile_id)}
    )
    if not document:
        raise HTTPException(status_code=404, detail="Profile not found")
    return serialize_profile(document)


@router.get("/{profile_id}/calls", response_model=CallHistoryResponse)
async def get_profile_calls(
    profile_id: str,
    query: CallHistoryQuery = Depends(),
) -> CallHistoryResponse:
    profile_object_id(profile_id)
    database = await get_database()
    calls = database["calls"]
    filters = {"profile_id": profile_id}
    documents = await calls.find(filters).sort("created_at", -1).skip(
        (query.page - 1) * query.limit
    ).limit(query.limit).to_list(length=query.limit)
    return CallHistoryResponse(
        items=[CallItemResponse(**document) for document in documents],
        page=query.page,
        limit=query.limit,
        total=await calls.count_documents(filters),
    )
