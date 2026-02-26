# Post-Call Processing Workflow

## Objective
Process Retell AI `call_analyzed` webhook events to create, reschedule, or cancel Google Calendar events for discovery meetings.

## Trigger
`POST /webhook/retell` — fired by Retell when call analysis is complete.

## Pipeline

1. **Receive webhook** — FastAPI endpoint at `/webhook/retell`
2. **Verify signature** — Check `x-retell-signature` header against `RETELL_API_KEY` (skipped in development)
3. **Parse payload** — Validate against `WebhookPayload` Pydantic model
4. **Determine outcome** — Read `custom_analysis_data.call_outcome` from Retell's post-call analysis:
   - `meeting_booked` → create new calendar event
   - `meeting_canceled` → find and delete existing calendar event
   - `meeting_rescheduled` → find and delete existing event, create new one at updated time
   - `callback_requested` → log only (future: handler)
   - `info_only` → log only
5. **Extract details** — Pull caller name, phone, meeting type, datetime from `custom_analysis_data`
6. **Execute action** — Create, delete, or reschedule calendar event
7. **Return 200** — Acknowledge receipt to Retell

## Tools Used
- `app/routers/retell_webhook.py` — webhook endpoint
- `app/services/call_parser.py` — outcome detection + data extraction
- `app/handlers/meeting_handler.py` — calendar event creation orchestration
- `app/services/google_calendar.py` — Google Calendar API wrapper

## Inputs
- Retell `call_analyzed` webhook payload (JSON)
- `RETELL_API_KEY` for signature verification
- `GOOGLE_TOKEN_JSON` for calendar authentication
- `GOOGLE_CALENDAR_ID` for target calendar

## Outputs
- Google Calendar event with:
  - Summary: "Discovery Meeting - [Name] ([Meeting Type])"
  - Time: 1 hour at the booked slot (HST)
  - Description: client name, phone, meeting type, call ID, call summary

## Edge Cases
- **Missing custom_analysis_data**: Falls back to parsing `transcript_with_tool_calls` for `check_available_dates` tool invocations
- **Unparseable datetime**: Tries 7 common formats; logs error if none match
- **Expired Google token**: Auto-refreshes using the refresh token
- **Short/failed calls**: Classified as `no_conversation`, no action taken
- **Duplicate webhooks**: Retell may retry on non-200 responses; calendar events include `call_id` in description for identification
- **Cancel with no matching event**: Logs a warning but returns 200 (caller may have already cancelled via other means)
- **Reschedule with no existing event**: Logs a warning but still creates the new event at the updated time

## Known Slot Times
Discovery meetings are always 1 hour:
- Morning: 10:00 AM - 11:00 AM HST
- Afternoon: 1:00 PM - 2:00 PM HST

## Retell Custom Analysis Fields Required
These must be configured in the Retell dashboard (see `retell_agent_config.md`):
- `call_outcome` (selector: meeting_booked, meeting_canceled, meeting_rescheduled, callback_requested, info_only)
- `caller_name` (text)
- `caller_phone` (text)
- `meeting_type` (selector: video, phone, in-person)
- `meeting_datetime` (text: YYYY-MM-DD HH:MM format)
