from fastapi import APIRouter, Depends, HTTPException, status
from app.database import check_mongodb_connection, close_db_connection

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}