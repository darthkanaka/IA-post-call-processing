import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from app.config import settings
from app.models import CancelDetails, MeetingDetails, MeetingType

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


def find_event_by_caller(caller_name: str, caller_phone: str) -> Optional[dict]:
    """Search for an upcoming calendar event matching the caller's name or phone."""
    service = _get_calendar_service()

    # Search future events only
    now = datetime.utcnow().isoformat() + "Z"

    # Search by caller name in event summary
    events_result = (
        service.events()
        .list(
            calendarId=settings.google_calendar_id,
            timeMin=now,
            maxResults=50,
            singleEvents=True,
            orderBy="startTime",
            q=caller_name,
        )
        .execute()
    )
    events = events_result.get("items", [])

    # Try to match by name in summary or phone in description
    for event in events:
        summary = event.get("summary", "")
        description = event.get("description", "")
        if caller_name.lower() in summary.lower():
            return event
        if caller_phone and caller_phone in description:
            return event

    # If name didn't match, try searching by phone number
    if caller_phone:
        events_result = (
            service.events()
            .list(
                calendarId=settings.google_calendar_id,
                timeMin=now,
                maxResults=50,
                singleEvents=True,
                orderBy="startTime",
                q=caller_phone,
            )
            .execute()
        )
        for event in events_result.get("items", []):
            description = event.get("description", "")
            if caller_phone in description:
                return event

    return None


def delete_calendar_event(event_id: str) -> None:
    """Delete a calendar event by its ID."""
    service = _get_calendar_service()
    service.events().delete(
        calendarId=settings.google_calendar_id, eventId=event_id
    ).execute()
    logger.info(f"Calendar event deleted: {event_id}")
