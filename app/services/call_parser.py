import json
import logging
from datetime import datetime
from typing import Optional

from app.models import CallData, CallOutcome, CancelDetails, MeetingDetails, MeetingType

logger = logging.getLogger(__name__)


def parse_call_outcome(call: CallData) -> CallOutcome:
    """Determine call outcome from custom_analysis_data, with fallbacks."""
    # Primary: check custom_analysis_data from Retell's post-call analysis
    if call.call_analysis and call.call_analysis.custom_analysis_data:
        outcome_str = call.call_analysis.custom_analysis_data.get("call_outcome", "")
        try:
            return CallOutcome(outcome_str)
        except ValueError:
            logger.warning(f"Unknown call_outcome value: {outcome_str}")

    # Fallback: check if check_available_dates tool was called (implies booking intent)
    if call.transcript_with_tool_calls:
        for item in call.transcript_with_tool_calls:
            if (
                item.get("role") == "tool_call_invocation"
                and item.get("name") == "check_available_dates"
            ):
                return CallOutcome.MEETING_BOOKED

    # Default
    if call.call_analysis and call.call_analysis.call_successful:
        return CallOutcome.INFO_ONLY

    return CallOutcome.NO_CONVERSATION


def extract_meeting_details(call: CallData) -> Optional[MeetingDetails]:
    """Extract meeting details from custom_analysis_data, with tool call fallback."""
    cad = {}
    if call.call_analysis and call.call_analysis.custom_analysis_data:
        cad = call.call_analysis.custom_analysis_data

    caller_name = cad.get("caller_name", "Unknown Caller")
    caller_phone = cad.get("caller_phone") or call.from_number or "Unknown"
    meeting_type_str = cad.get("meeting_type", "phone")
    meeting_datetime_str = cad.get("meeting_datetime", "")

    # Fallback: try to extract datetime from tool call arguments
    if not meeting_datetime_str and call.transcript_with_tool_calls:
        meeting_datetime_str = _extract_datetime_from_tool_calls(
            call.transcript_with_tool_calls
        )

    if not meeting_datetime_str:
        logger.error(f"No meeting datetime found for call {call.call_id}")
        return None

    # Parse the datetime string
    try:
        dt = _parse_flexible_datetime(meeting_datetime_str)
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M")
    except ValueError as e:
        logger.error(f"Could not parse datetime '{meeting_datetime_str}': {e}")
        return None

    # Determine duration from known slot times (10-11 morning, 1-2 afternoon)
    duration_minutes = 60

    try:
        meeting_type = MeetingType(meeting_type_str.lower().strip())
    except ValueError:
        meeting_type = MeetingType.PHONE

    return MeetingDetails(
        caller_name=caller_name,
        caller_phone=caller_phone,
        meeting_type=meeting_type,
        date_str=date_str,
        time_str=time_str,
        duration_minutes=duration_minutes,
        call_summary=call.call_analysis.call_summary if call.call_analysis else None,
        call_id=call.call_id,
    )


def extract_cancel_details(call: CallData) -> Optional[CancelDetails]:
    """Extract caller info for cancellation or as the 'old meeting' in a reschedule."""
    cad = {}
    if call.call_analysis and call.call_analysis.custom_analysis_data:
        cad = call.call_analysis.custom_analysis_data

    caller_name = cad.get("caller_name", "Unknown Caller")
    caller_phone = cad.get("caller_phone") or call.from_number or "Unknown"

    if caller_name == "Unknown Caller" and caller_phone == "Unknown":
        logger.error(f"No caller info found for cancel/reschedule on call {call.call_id}")
        return None

    return CancelDetails(
        caller_name=caller_name,
        caller_phone=caller_phone,
        call_summary=call.call_analysis.call_summary if call.call_analysis else None,
        call_id=call.call_id,
    )


def _extract_datetime_from_tool_calls(transcript_with_tool_calls: list[dict]) -> str:
    """Parse tool call invocations to find the selected meeting time."""
    for item in transcript_with_tool_calls:
        if (
            item.get("role") == "tool_call_invocation"
            and item.get("name") == "check_available_dates"
        ):
            try:
                args = json.loads(item.get("arguments", "{}"))
                date = args.get("date", "")
                time = args.get("time", "")
                if date and time:
                    return f"{date} {time}"
                if date:
                    return date
            except json.JSONDecodeError:
                continue
    return ""


def _parse_flexible_datetime(dt_str: str) -> datetime:
    """Try multiple datetime formats to handle LLM output variation."""
    formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%dT%H:%M",
        "%m/%d/%Y %H:%M",
        "%B %d, %Y %H:%M",
        "%B %d, %Y %I:%M %p",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(dt_str.strip(), fmt)
        except ValueError:
            continue
    raise ValueError(f"No matching datetime format for: {dt_str}")
