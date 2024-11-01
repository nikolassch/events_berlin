import pandas as pd
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
from bs4 import BeautifulSoup

# OAuth 2.0 flow
SCOPES = ['https://www.googleapis.com/auth/calendar']
flow = InstalledAppFlow.from_client_secrets_file(
    'credentials_google_calendar_api.json',
    SCOPES
)
creds = flow.run_local_server(port=0)

def create_events_calendar():
   
    # Build the service
    service = build('calendar', 'v3', credentials=creds)
    
    # Create new calendar
    calendar = {
        'summary': 'events',
        'timeZone': 'Europe/Berlin'
    }
    
    try:
        created_calendar = service.calendars().insert(body=calendar).execute()
        print(f'Created calendar: {created_calendar["id"]}')
        return created_calendar['id']
    except Exception as e:
        print(f'An error occurred: {e}')
        return None

# Create the calendar
calendar_id = create_events_calendar()