import json
import logging
from datetime import datetime, timedelta

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from app.config import settings
from app.models import MeetingDetails, MeetingType

logger = logging.getLogger(__name__)

HST_TIMEZONE = "Pacific/Honolulu"


def _get_calendar_service():
    """Build and return an authenticated Google Calendar service."""
    token_data = json.loads(settings.google_token_json)
    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri=token_data.get("token_uri"),
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=token_data.get("scopes"),
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        logger.info("Google OAuth token refreshed")

    return build("calendar", "v3", credentials=creds)


def create_calendar_event(meeting: MeetingDetails) -> dict:
    """Create a Google Calendar event from meeting details."""
    service = _get_calendar_service()

    start_dt = datetime.strptime(
        f"{meeting.date_str} {meeting.time_str}", "%Y-%m-%d %H:%M"
    )
    end_dt = start_dt + timedelta(minutes=meeting.duration_minutes)

    type_labels = {
        MeetingType.VIDEO: "Video Call",
        MeetingType.PHONE: "Phone Call",
        MeetingType.IN_PERSON: "In-Person Meeting",
    }
    type_label = type_labels.get(meeting.meeting_type, "Meeting")

    summary = f"Discovery Meeting - {meeting.caller_name} ({type_label})"

    description_parts = [
        f"Client: {meeting.caller_name}",
        f"Phone: {meeting.caller_phone}",
        f"Meeting Type: {type_label}",
        f"Call ID: {meeting.call_id}",
    ]
    if meeting.call_summary:
        description_parts.append(f"\nCall Summary:\n{meeting.call_summary}")

    event_body = {
        "summary": summary,
        "description": "\n".join(description_parts),
        "start": {
            "dateTime": start_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": HST_TIMEZONE,
        },
        "end": {
            "dateTime": end_dt.strftime("%Y-%m-%dT%H:%M:%S"),
            "timeZone": HST_TIMEZONE,
        },
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 30},
            ],
        },
    }

    event = (
        service.events()
        .insert(calendarId=settings.google_calendar_id, body=event_body)
        .execute()
    )

    return event
