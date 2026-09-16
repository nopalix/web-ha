import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from app.config import settings

SCOPES = ['https://www.googleapis.com/auth/calendar']

def create_calendar_event(summary: str, description: str, limite_date: str, location: str = None):
    if not settings.GOOGLE_CREDENTIALS_FILE or not os.path.exists(settings.GOOGLE_CREDENTIALS_FILE):
        print("Google Calendar credentials file not found.")
        return

    if not limite_date:
        print("No limit date provided for calendar event.")
        return

    creds = None
    token_path = os.path.join(os.path.dirname(__file__), "../token.json")
    
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None
        if not creds:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    settings.GOOGLE_CREDENTIALS_FILE, SCOPES
                )
                creds = flow.run_local_server(port=0)
                with open(token_path, "w") as token:
                    token.write(creds.to_json())
            except Exception as e:
                print(f"OAuth2 Flow error (Note: interactive browser login required if running locally): {e}")
                return

    try:
        service = build('calendar', 'v3', credentials=creds)
        start_datetime = f"{limite_date}T08:00:00"
        end_datetime = f"{limite_date}T09:00:00"

        event = {
            'summary': summary,
            'description': description or '',
            'location': location or '',
            'start': {'dateTime': start_datetime, 'timeZone': 'UTC'},
            'end': {'dateTime': end_datetime, 'timeZone': 'UTC'},
        }
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Google Calendar Event created: {created_event.get('htmlLink')}")
    except Exception as e:
        print(f"Error creating Google Calendar event: {e}")
