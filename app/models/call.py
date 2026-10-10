from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class QualificationOutcome(BaseModel):
    call_outcome: Optional[str] = Field(None, description="Call outcome: qualified, disqualified, transfer, callback, not_interested, wrong_person")
    property_type: Optional[str] = Field(None, description="Property type: residential, commercial, industrial, agricultural")
    ownership_status: Optional[str] = Field(None, description="Ownership status: sole, joint")
    original_documents: Optional[bool] = Field(None, description="Whether original documents are available")
    loan_amount: Optional[float] = Field(None, description="Loan amount in INR")
    occupation: Optional[str] = Field(None, description="Occupation: salaried, self_employed")
    income_mode: Optional[str] = Field(None, description="Income mode: bank, cash")
    market_value: Optional[float] = Field(None, description="Market value of property in INR")
    tenure_years: Optional[float] = Field(None, description="Loan tenure in years")
    disqualification_reason: str = Field("", description="Reason for disqualification")
    transfer_reason: str = Field("", description="Reason for transfer")

    def to_selector_values(self) -> Dict[str, str]:
        """Normalize selector values."""
        result = {}
        if self.call_outcome:
            result["call_outcome"] = self.call_outcome.lower().replace(" ", "_")
        if self.property_type:
            result["property_type"] = self.property_type.lower().replace(" ", "_")
        if self.ownership_status:
            result["ownership_status"] = self.ownership_status.lower().replace(" ", "_")
        if self.occupation:
            result["occupation"] = self.occupation.lower().replace(" ", "_")
        if self.income_mode:
            result["income_mode"] = self.income_mode.lower().replace(" ", "_")
        return result


class CallBase(BaseModel):
    retell_call_id: str
    agent_id: str
    customer_name: str
    call_status: str
    call_type: str
    start_timestamp: Optional[float] = None
    end_timestamp: Optional[float] = None
    duration_ms: Optional[int] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    call_summary: Optional[str] = None
    call_successful: Optional[bool] = None
    user_sentiment: Optional[str] = None
    qualification: Optional[QualificationOutcome] = None
    created_at: Optional[float] = None
    updated_at: Optional[float] = None


class CallCreate(CallBase):
    pass


class CallUpdate(BaseModel):
    call_status: Optional[str] = None
    end_timestamp: Optional[float] = None
    duration_ms: Optional[int] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    call_summary: Optional[str] = None
    call_successful: Optional[bool] = None
    user_sentiment: Optional[str] = None
    qualification: Optional[QualificationOutcome] = None
    updated_at: float = Field(default_factory=lambda: __import__("time").time())


class CallResponse(BaseModel):
    retell_call_id: str
    agent_id: str
    customer_name: str
    call_status: str
    call_type: str
    start_timestamp: Optional[float] = None
    end_timestamp: Optional[float] = None
    duration_ms: Optional[int] = None
    recording_url: Optional[str] = None
    transcript: Optional[str] = None
    call_summary: Optional[str] = None
    call_successful: Optional[bool] = None
    user_sentiment: Optional[str] = None
    qualification: Optional[Dict[str, Any]] = None
    created_at: Optional[float] = None
    updated_at: Optional[float] = None
    id: Optional[str] = None

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }