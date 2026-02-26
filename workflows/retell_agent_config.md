# Retell Agent Configuration Workflow

## Objective
Configure the Marina agent's post-call analysis fields so the webhook receives structured booking data.

## Steps

### 1. Open Retell Dashboard
Navigate to the Marina agent settings.

### 2. Set Webhook URL
Under **Agent Level Webhook URL**, enter your Railway deployment URL:
```
https://your-app.up.railway.app/webhook/retell
```

### 3. Configure Post-Call Analysis Fields
Navigate to the post-call analysis configuration and create these 5 custom fields:

#### Field 1: call_outcome
- **Name**: `call_outcome`
- **Type**: Selector
- **Options**: `meeting_booked`, `callback_requested`, `info_only`
- **Description/Prompt**: "Classify the outcome of this call. Use 'meeting_booked' if the caller confirmed an appointment, 'callback_requested' if they wanted someone to call them back, or 'info_only' if they just asked questions."

#### Field 2: caller_name
- **Name**: `caller_name`
- **Type**: Text
- **Description/Prompt**: "Extract the full name of the caller as stated during the conversation. Leave empty if not provided."

#### Field 3: caller_phone
- **Name**: `caller_phone`
- **Type**: Text
- **Description/Prompt**: "Extract the caller's phone number if they provided one during the conversation. Format as provided. Leave empty if not stated."

#### Field 4: meeting_type
- **Name**: `meeting_type`
- **Type**: Selector
- **Options**: `video`, `phone`, `in-person`
- **Description/Prompt**: "What type of meeting did the caller request? Select the meeting format they chose."

#### Field 5: meeting_datetime
- **Name**: `meeting_datetime`
- **Type**: Text
- **Description/Prompt**: "Extract the exact date and time the caller chose for their discovery meeting. Format as YYYY-MM-DD HH:MM in 24-hour time. For example, March 3rd at 10 AM should be '2026-03-03 10:00'. Leave empty if no meeting was booked."

### 4. Verify
Make a test call to Marina, book a meeting, and check:
1. Railway logs show the webhook was received
2. `custom_analysis_data` contains all 5 fields
3. A calendar event appears at the correct time

## Notes
- These fields are populated by Retell's LLM during its standard post-call analysis — no additional API cost
- The `meeting_datetime` prompt explicitly asks for `YYYY-MM-DD HH:MM` format to minimize parsing issues
- If a field is empty or missing, the system falls back to parsing the transcript and tool calls
