from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class CallStartRequest(BaseModel):
    profile_id: str = Field(..., description="MongoDB profile ID")
    agent_name: str = Field(default="Ananya", min_length=1, max_length=100)


class CallStartResponse(BaseModel):
    call_id: str = Field(..., description="Retell call ID")
    access_token: str = Field(..., description="Access token for Retell Web SDK")
    transport: Optional[str] = Field(None, description="Retell media transport")
    ice_servers: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="WebRTC ICE server configuration",
    )


class WebhookPayload(BaseModel):
    event: str = Field(..., description="Event type: call_started, call_ended, call_analyzed")
    call_id: str = Field(..., description="Retell call ID")
    data: Optional[Dict[str, Any]] = Field(None, description="Event data")


class WebhookCallStarted(BaseModel):
    event: str = "call_started"
    call_id: str


class WebhookCallEnded(BaseModel):
    event: str = "call_ended"
    call_id: str


class WebhookCallAnalyzed(BaseModel):
    event: str = "call_analyzed"
    call_id: str


class CallHistoryQuery(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    outcome: Optional[str] = Field(None, description="Filter by qualification.call_outcome")
    profile_id: Optional[str] = Field(None, description="Filter by profile ID")


class CallItemResponse(BaseModel):
    retell_call_id: str
    profile_id: Optional[str] = None
    agent_id: str
    customer_name: str
    call_status: str
    call_type: str
    call_summary: Optional[str] = None
    call_successful: Optional[bool] = None
    user_sentiment: Optional[str] = None
    qualification: Optional[Dict[str, Any]] = None
    start_timestamp: Optional[float] = None
    end_timestamp: Optional[float] = None
    duration_ms: Optional[int] = None
    created_at: Optional[float] = None


class CallResponse(BaseModel):
    retell_call_id: str
    profile_id: Optional[str] = None
    agent_id: str
    customer_name: str
    call_status: str
    call_type: str
    start_timestamp: Optional[float] = None
    end_timestamp: Optional[float] = None
    duration_ms: Optional[int] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    transcript_object: Optional[List[Dict[str, Any]]] = None
    transcript_with_tool_calls: Optional[List[Dict[str, Any]]] = None
    call_summary: Optional[str] = None
    call_successful: Optional[bool] = None
    user_sentiment: Optional[str] = None
    qualification: Optional[Dict[str, Any]] = None
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
    id: Optional[str] = None

    model_config = {
        "populate_by_name": True,
    }


class CallHistoryResponse(BaseModel):
    items: List[CallItemResponse]
    page: int
    limit: int
    total: int
