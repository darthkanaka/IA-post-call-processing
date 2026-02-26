# Google OAuth Setup Workflow

## Objective
Generate a Google OAuth token for Calendar API access and deploy it as an environment variable.

## When to Run
- First-time setup
- If the refresh token is revoked (user removes app access in Google Account settings)
- If the Google project credentials change

## Steps

### 1. Run the token generator locally
```bash
cd "/Users/veex/Documents/Developer/Inviz Arts Post Call Processing"
PYTHONPATH=. python3 tools/generate_token.py
```

### 2. Authorize in browser
- A browser window opens to Google's OAuth consent screen
- Sign in with the Invisible Arts Google account
- Grant Calendar access
- The browser redirects to localhost and the script completes

### 3. Copy the token JSON
The script outputs a JSON string. Copy everything between the `===` markers.

### 4. Set the environment variable
- **Local (.env)**: Paste as the value of `GOOGLE_TOKEN_JSON`
- **Railway**: Go to project settings → Variables → set `GOOGLE_TOKEN_JSON`

## How Token Refresh Works
- The access token expires after ~1 hour
- The app automatically refreshes it using the `refresh_token`
- The refresh token itself does not expire unless:
  - The user revokes access at https://myaccount.google.com/permissions
  - The token limit (100 per client ID) is exceeded
  - The Google Cloud project is deleted

## Files
- `Credentials.json` — Google OAuth client credentials (desktop type)
- `token.json` — Generated locally by the script (gitignored)
- `tools/generate_token.py` — The token generation script

## Troubleshooting
- **"Access blocked" in browser**: The Google Cloud project may need the OAuth consent screen configured. Go to Google Cloud Console → APIs & Services → OAuth consent screen.
- **"Token has been expired or revoked"**: Re-run `tools/generate_token.py` and update the env var.
- **Wrong calendar**: Check `GOOGLE_CALENDAR_ID` in .env. Use `primary` for the default calendar or a specific calendar ID.
