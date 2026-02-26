from pydantic import BaseModel
from typing import Optional, Any
from enum import Enum


class WebhookEventType(str, Enum):
    CALL_STARTED = "call_started"
    CALL_ENDED = "call_ended"
    CALL_ANALYZED = "call_analyzed"


class CallOutcome(str, Enum):
    MEETING_BOOKED = "meeting_booked"
    MEETING_CANCELLED = "meeting_canceled"
    MEETING_RESCHEDULED = "meeting_rescheduled"
    CALLBACK_REQUESTED = "callback_requested"
    INFO_ONLY = "info_only"
    NO_CONVERSATION = "no_conversation"


class MeetingType(str, Enum):
    VIDEO = "video"
    PHONE = "phone"
    IN_PERSON = "in-person"


class CallAnalysis(BaseModel):
    call_summary: Optional[str] = None
    user_sentiment: Optional[str] = None
    call_successful: Optional[bool] = None
    in_voicemail: Optional[bool] = None
    custom_analysis_data: Optional[dict[str, Any]] = None


class CallData(BaseModel):
    call_id: str
    agent_id: Optional[str] = None
    call_type: Optional[str] = None
    call_status: Optional[str] = None
    from_number: Optional[str] = None
    to_number: Optional[str] = None
    direction: Optional[str] = None
    start_timestamp: Optional[int] = None
    end_timestamp: Optional[int] = None
    duration_ms: Optional[int] = None
    disconnection_reason: Optional[str] = None
    transcript: Optional[str] = None
    transcript_object: Optional[list[dict]] = None
    transcript_with_tool_calls: Optional[list[dict]] = None
    call_analysis: Optional[CallAnalysis] = None
    metadata: Optional[dict[str, Any]] = None
    retell_llm_dynamic_variables: Optional[dict[str, Any]] = None
    collected_dynamic_variables: Optional[dict[str, Any]] = None

    model_config = {"extra": "allow"}


class WebhookPayload(BaseModel):
    event: WebhookEventType
    call: CallData


class MeetingDetails(BaseModel):
    """Extracted and validated meeting details ready for calendar creation."""
    caller_name: str
    caller_phone: str
    meeting_type: MeetingType
    date_str: str          # e.g. "2026-03-03"
    time_str: str          # e.g. "10:00"
    duration_minutes: int = 60  # Slots are 1 hour (10-11 or 1-2)
    call_summary: Optional[str] = None
    call_id: str


class CancelDetails(BaseModel):
    """Extracted details for cancelling an existing meeting."""
    caller_name: str
    caller_phone: str
    call_summary: Optional[str] = None
    call_id: str
