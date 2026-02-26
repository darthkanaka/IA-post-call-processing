import logging

from app.models import MeetingDetails
from app.services.google_calendar import create_calendar_event

logger = logging.getLogger(__name__)


async def handle_meeting_booked(meeting: MeetingDetails) -> None:
    """Create a Google Calendar event for the booked meeting."""
    logger.info(
        f"Creating calendar event for {meeting.caller_name} "
        f"on {meeting.date_str} at {meeting.time_str}"
    )
    try:
        event = create_calendar_event(meeting)
        logger.info(f"Calendar event created: {event.get('htmlLink', 'no link')}")
    except Exception as e:
        logger.error(
            f"Failed to create calendar event for call {meeting.call_id}: {e}",
            exc_info=True,
        )
        raise
