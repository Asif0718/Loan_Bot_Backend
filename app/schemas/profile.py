from typing import Any

from pydantic import BaseModel, Field


class ProfileCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=200)
    language_to_speak: str = Field(default="English", min_length=1, max_length=50)
    phone: str | None = Field(default=None, max_length=30)
    dynamic_variables: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProfileResponse(ProfileCreate):
    id: str
    created_at: float
    updated_at: float


class ProfileListResponse(BaseModel):
    items: list[ProfileResponse]
    page: int
    limit: int
    total: int
