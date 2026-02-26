"""
Sends a mock call_analyzed webhook payload to the local server.
Skips signature verification (server must be running with ENVIRONMENT=development).

Usage: python tools/test_webhook.py [--url http://localhost:8000/webhook/retell]
"""

import argparse
import json

import requests

MOCK_MEETING_BOOKED = {
    "event": "call_analyzed",
    "call": {
        "call_id": "test_call_001",
        "agent_id": "agent_marina",
        "call_type": "phone_call",
        "from_number": "+18081234567",
        "to_number": "+18089876543",
        "direction": "inbound",
        "call_status": "ended",
        "start_timestamp": 1708900000000,
        "end_timestamp": 1708900300000,
        "duration_ms": 300000,
        "disconnection_reason": "agent_hangup",
        "transcript": "Agent: Hello, this is Marina with Invisible Arts. How can I help you today?\nUser: Hi, I'm interested in your web design services.\nAgent: That's right in our wheelhouse. Want me to check available times for a discovery call?\nUser: Yes please.\nAgent: I've got next Tuesday, March 3rd at 10 AM or Thursday, March 5th at 1 PM. Either of those work?\nUser: Tuesday at 10 works great.\nAgent: Perfect. What's the best number to reach you?\nUser: 808-555-1234.\nAgent: 808-555-1234, got it. Would you prefer a video call, phone call, or in person?\nUser: Video call.\nAgent: And what name should I put this under?\nUser: John Smith.\nAgent: You're all set for Tuesday, March 3rd at 10 AM for a video call. We look forward to connecting with you, John.",
        "transcript_with_tool_calls": [
            {"role": "agent", "content": "Let me check available times for you."},
            {
                "role": "tool_call_invocation",
                "tool_call_id": "tc_001",
                "name": "check_available_dates",
                "arguments": "{}",
            },
            {
                "role": "tool_call_result",
                "tool_call_id": "tc_001",
                "content": "[{\"date\": \"2026-03-03\", \"time\": \"morning\", \"start\": \"10:00\", \"end\": \"11:00\"}, {\"date\": \"2026-03-05\", \"time\": \"afternoon\", \"start\": \"13:00\", \"end\": \"14:00\"}]",
                "successful": True,
            },
        ],
        "call_analysis": {
            "call_summary": "Caller John Smith inquired about web design services and booked a video discovery meeting for Tuesday March 3rd at 10 AM HST.",
            "user_sentiment": "Positive",
            "call_successful": True,
            "in_voicemail": False,
            "custom_analysis_data": {
                "call_outcome": "meeting_booked",
                "caller_name": "John Smith",
                "caller_phone": "808-555-1234",
                "meeting_type": "video",
                "meeting_datetime": "2026-03-03 10:00",
            },
        },
    },
}

MOCK_INFO_ONLY = {
    "event": "call_analyzed",
    "call": {
        "call_id": "test_call_002",
        "agent_id": "agent_marina",
        "call_type": "phone_call",
        "from_number": "+18085559999",
        "direction": "inbound",
        "call_status": "ended",
        "duration_ms": 120000,
        "transcript": "Agent: Hello, this is Marina with Invisible Arts.\nUser: Hi, I just wanted to know what you guys do.\nAgent: We're a creative agency that handles web design, branding, and digital strategy.\nUser: Cool, thanks. I'll think about it.\nAgent: No problem. Anything else I can help with?\nUser: Nope, that's it. Thanks!\nAgent: Thanks for calling. Have a great day.",
        "call_analysis": {
            "call_summary": "Caller asked about services. No meeting booked.",
            "user_sentiment": "Neutral",
            "call_successful": True,
            "in_voicemail": False,
            "custom_analysis_data": {
                "call_outcome": "info_only",
                "caller_name": "",
                "caller_phone": "",
                "meeting_type": "",
                "meeting_datetime": "",
            },
        },
    },
}

MOCK_CANCEL = {
    "event": "call_analyzed",
    "call": {
        "call_id": "test_call_003",
        "agent_id": "agent_marina",
        "call_type": "phone_call",
        "from_number": "+18081234567",
        "direction": "inbound",
        "call_status": "ended",
        "duration_ms": 90000,
        "transcript": "Agent: Hello, this is Marina with Invisible Arts.\nUser: Hi, this is John Smith. I need to cancel my meeting.\nAgent: No problem, John. I'll take care of that for you.\nUser: Thanks.\nAgent: Your meeting has been cancelled. Is there anything else?\nUser: No, that's all.\nAgent: Thanks for calling, John. Have a great day.",
        "call_analysis": {
            "call_summary": "John Smith called to cancel his upcoming discovery meeting.",
            "user_sentiment": "Neutral",
            "call_successful": True,
            "in_voicemail": False,
            "custom_analysis_data": {
                "call_outcome": "meeting_canceled",
                "caller_name": "John Smith",
                "caller_phone": "808-555-1234",
                "meeting_type": "",
                "meeting_datetime": "",
            },
        },
    },
}

MOCK_RESCHEDULE = {
    "event": "call_analyzed",
    "call": {
        "call_id": "test_call_004",
        "agent_id": "agent_marina",
        "call_type": "phone_call",
        "from_number": "+18081234567",
        "direction": "inbound",
        "call_status": "ended",
        "duration_ms": 180000,
        "transcript": "Agent: Hello, this is Marina with Invisible Arts.\nUser: Hi, this is John Smith. I need to reschedule my meeting to Thursday.\nAgent: Sure, let me check what's available on Thursday.\nAgent: I have Thursday, March 5th at 1 PM. Does that work?\nUser: Perfect.\nAgent: You're all set for Thursday, March 5th at 1 PM. See you then, John.",
        "call_analysis": {
            "call_summary": "John Smith called to reschedule his discovery meeting from Tuesday to Thursday March 5th at 1 PM.",
            "user_sentiment": "Positive",
            "call_successful": True,
            "in_voicemail": False,
            "custom_analysis_data": {
                "call_outcome": "meeting_rescheduled",
                "caller_name": "John Smith",
                "caller_phone": "808-555-1234",
                "meeting_type": "video",
                "meeting_datetime": "2026-03-05 13:00",
            },
        },
    },
}

SCENARIOS = {
    "meeting": MOCK_MEETING_BOOKED,
    "info": MOCK_INFO_ONLY,
    "cancel": MOCK_CANCEL,
    "reschedule": MOCK_RESCHEDULE,
}


def main():
    parser = argparse.ArgumentParser(description="Send mock Retell webhook payloads")
    parser.add_argument("--url", default="http://localhost:8000/webhook/retell")
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        default="meeting",
        help="Which mock scenario to send",
    )
    args = parser.parse_args()

    payload = SCENARIOS[args.scenario]
    print(f"Sending '{args.scenario}' scenario to {args.url}")
    print(f"Payload event: {payload['event']}")

    resp = requests.post(args.url, json=payload)
    print(f"Status: {resp.status_code}")
    print(f"Response: {json.dumps(resp.json(), indent=2)}")


if __name__ == "__main__":
    main()
