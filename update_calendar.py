import pandas as pd
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import requests
from bs4 import BeautifulSoup
import glob
import os

# Constants at module level
SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = 'credentials_google_calendar_api.json'
CALENDAR_NAME = 'events'
TIMEZONE = 'Europe/Berlin'

def merge_event_files():
    # Get all CSV files starting with 'events_'
    event_files = glob.glob('events_*.csv')
    
    if not event_files:
        print("No event files found starting with 'events_'")
        return None
        
    # Read and combine all CSV files
    dfs = []
    for file in event_files:
        try:
            df = pd.read_csv(file)
            print(f"Loaded: {file}")
            dfs.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")
            
    if not dfs:
        print("No valid CSV files found")
        return None
        
    # Combine all dataframes
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Remove duplicates if any
    combined_df = combined_df.drop_duplicates()
    
    # Save combined file
    combined_df.to_csv('events.csv', index=False)
    print(f"Combined {len(dfs)} files into events.csv")
    
    return combined_df

def update_calendar():
    # First merge all event files
    df = merge_event_files()
    if df is None:
        return
        
    # OAuth 2.0 flow
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    
    # Filter for future events only
    current_date = datetime.now()
    df['datetime'] = pd.to_datetime(df['Date'])
    df = df[df['datetime'] >= current_date]
    
    # Build the service
    service = build('calendar', 'v3', credentials=creds)

    # Find the calendar
    calendar_list = service.calendarList().list().execute()
    events_calendar = next((calendar for calendar in calendar_list['items'] 
                          if calendar['summary'] == CALENDAR_NAME), None)

    if not events_calendar:
        print(f"Calendar '{CALENDAR_NAME}' not found. Please make sure it exists.")
        return

    calendar_id = events_calendar['id']

    # Get existing events
    existing_events = {}
    page_token = None
    while True:
        events = service.events().list(calendarId=calendar_id, pageToken=page_token).execute()
        for event in events['items']:
            existing_events[event['summary']] = event['id']
        page_token = events.get('nextPageToken')
        if not page_token:
            break

    # Add or update events
    for _, row in df.iterrows():
        event_date = pd.to_datetime(row['Date'])
        event_end = event_date + timedelta(hours=2)
        
        event = {
            'summary': row['Name'],
            'description': f"More info: {row['Link']}" if row['Link'] else "",
            'location': row['Location'],
            'start': {
                'dateTime': event_date.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': TIMEZONE,
            },
            'end': {
                'dateTime': event_end.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': TIMEZONE,
            },
        }
        
        try:
            if row['Name'] in existing_events:
                service.events().update(
                    calendarId=calendar_id,
                    eventId=existing_events[row['Name']],
                    body=event
                ).execute()
                print(f"Updated event: {row['Name']}")
            else:
                service.events().insert(calendarId=calendar_id, body=event).execute()
                print(f"Added event: {row['Name']}")
        except Exception as e:
            print(f"Error processing event {row['Name']}: {e}")

if __name__ == "__main__":
    update_calendar()
