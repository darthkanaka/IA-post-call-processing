import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from retell import Retell

from app.config import settings
from app.models import WebhookPayload, WebhookEventType
from app.models import CallOutcome
from app.services.call_parser import parse_call_outcome, extract_meeting_details, extract_cancel_details
from app.handlers.meeting_handler import handle_meeting_booked, handle_meeting_cancelled, handle_meeting_rescheduled

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook/retell")
async def handle_webhook(request: Request):
    post_data = await request.json()

    # Verify signature in production
    if settings.environment != "development":
        retell = Retell(api_key=settings.retell_api_key)
        valid_signature = retell.verify(
            json.dumps(post_data, separators=(",", ":"), ensure_ascii=False),
            api_key=settings.retell_api_key,
            signature=str(request.headers.get("x-retell-signature", "")),
        )
        if not valid_signature:
            logger.warning("Invalid webhook signature received")
            return JSONResponse(status_code=401, content={"message": "Unauthorized"})

    payload = WebhookPayload(**post_data)

    if payload.event == WebhookEventType.CALL_STARTED:
        logger.info(f"Call started: {payload.call.call_id}")

    elif payload.event == WebhookEventType.CALL_ENDED:
        logger.info(f"Call ended: {payload.call.call_id}")

    elif payload.event == WebhookEventType.CALL_ANALYZED:
        logger.info(f"Call analyzed: {payload.call.call_id}")
        outcome = parse_call_outcome(payload.call)
        logger.info(f"Call outcome: {outcome.value} for {payload.call.call_id}")

        if outcome == CallOutcome.MEETING_BOOKED:
            meeting = extract_meeting_details(payload.call)
            if meeting:
                await handle_meeting_booked(meeting)
            else:
                logger.error(f"Could not extract meeting details from call {payload.call.call_id}")

        elif outcome == CallOutcome.MEETING_CANCELLED:
            cancel = extract_cancel_details(payload.call)
            if cancel:
                await handle_meeting_cancelled(cancel)
            else:
                logger.error(f"Could not extract cancel details from call {payload.call.call_id}")

        elif outcome == CallOutcome.MEETING_RESCHEDULED:
            cancel = extract_cancel_details(payload.call)
            meeting = extract_meeting_details(payload.call)
            if cancel and meeting:
                await handle_meeting_rescheduled(cancel, meeting)
            else:
                logger.error(f"Could not extract reschedule details from call {payload.call.call_id}")

    return JSONResponse(status_code=200, content={"received": True})
