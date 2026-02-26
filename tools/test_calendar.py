"""
Test script to verify Google Calendar credentials work.
Creates a test event, prints confirmation, then deletes it.

Usage: python tools/test_calendar.py
"""

from datetime import datetime, timedelta

from app.services.google_calendar import _get_calendar_service
from app.config import settings


def main():
    print("Connecting to Google Calendar...")
    service = _get_calendar_service()

    tomorrow = datetime.now() + timedelta(days=1)
    test_event = {
        "summary": "TEST - Post Call Processor Verification",
        "description": "Automated test event. Should be deleted automatically.",
        "start": {
            "dateTime": tomorrow.replace(hour=10, minute=0, second=0).strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),
            "timeZone": "Pacific/Honolulu",
        },
        "end": {
            "dateTime": tomorrow.replace(hour=10, minute=30, second=0).strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),
            "timeZone": "Pacific/Honolulu",
        },
    }

    event = (
        service.events()
        .insert(calendarId=settings.google_calendar_id, body=test_event)
        .execute()
    )
    print(f"Test event created: {event['htmlLink']}")

    service.events().delete(
        calendarId=settings.google_calendar_id, eventId=event["id"]
    ).execute()
    print("Test event deleted. Google Calendar integration is working!")


if __name__ == "__main__":
    main()
