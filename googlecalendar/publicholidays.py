from __future__ import print_function
import datetime
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


''' i have a calendar with egyptian holidays set on my google account'''
def get_egypt_public_holidays(year):
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('googlecalendar/token.pickle'):
        with open('googlecalendar/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'googlecalendar/credentials.json', SCOPES)
            creds = flow
        # Save the credentials for the next run
        with open('googlecalendar/token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    min = datetime.datetime(year, 1, 1).isoformat() +'Z'
    max = datetime.datetime(year+1, 1, 1).isoformat() +'Z'
    print(str(min))
    print('Getting the upcoming 10 events')
    events_result = service.events().list(calendarId='en-gb.eg#holiday@group.v.calendar.google.com', timeMin=min, timeMax=max,
                                        maxResults=1000, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
        return None

    service.close()
    return events
    

# if __name__ == '__main__':
#     main()