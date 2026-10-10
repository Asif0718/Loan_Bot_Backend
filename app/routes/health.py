from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.api_route("", methods=["GET", "HEAD"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
