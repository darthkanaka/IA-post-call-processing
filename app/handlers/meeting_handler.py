import logging

from app.models import CancelDetails, MeetingDetails
from app.services.google_calendar import (
    create_calendar_event,
    delete_calendar_event,
    find_event_by_caller,
)

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


async def handle_meeting_cancelled(details: CancelDetails) -> None:
    """Find and delete the caller's existing calendar event."""
    logger.info(f"Cancelling meeting for {details.caller_name}")
    try:
        event = find_event_by_caller(details.caller_name, details.caller_phone)
        if event:
            delete_calendar_event(event["id"])
            logger.info(
                f"Meeting cancelled for {details.caller_name}: {event.get('summary')}"
            )
        else:
            logger.warning(
                f"No matching event found to cancel for {details.caller_name} "
                f"({details.caller_phone})"
            )
    except Exception as e:
        logger.error(
            f"Failed to cancel meeting for call {details.call_id}: {e}",
            exc_info=True,
        )
        raise


async def handle_meeting_rescheduled(
    cancel: CancelDetails, new_meeting: MeetingDetails
) -> None:
    """Delete the old event and create a new one at the updated time."""
    logger.info(
        f"Rescheduling meeting for {cancel.caller_name} "
        f"to {new_meeting.date_str} at {new_meeting.time_str}"
    )
    try:
        # Delete the old event
        event = find_event_by_caller(cancel.caller_name, cancel.caller_phone)
        if event:
            delete_calendar_event(event["id"])
            logger.info(f"Old event deleted: {event.get('summary')}")
        else:
            logger.warning(
                f"No existing event found for {cancel.caller_name} — "
                f"creating new event anyway"
            )

        # Create the new event
        new_event = create_calendar_event(new_meeting)
        logger.info(
            f"Rescheduled event created: {new_event.get('htmlLink', 'no link')}"
        )
    except Exception as e:
        logger.error(
            f"Failed to reschedule meeting for call {cancel.call_id}: {e}",
            exc_info=True,
        )
        raise
