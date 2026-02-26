"""
One-time local script to generate Google OAuth token.
Run this locally, then copy the output JSON into the GOOGLE_TOKEN_JSON env var.

Usage: python tools/generate_token.py
"""

import json
import os

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS_FILE = "Credentials.json"
TOKEN_FILE = "token.json"


def main():
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())

    token_data = json.loads(creds.to_json())
    print("\n=== Copy the following into your GOOGLE_TOKEN_JSON environment variable ===\n")
    print(json.dumps(token_data))
    print("\n=== End of token JSON ===")


if __name__ == "__main__":
    main()
