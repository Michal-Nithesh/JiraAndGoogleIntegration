import requests
from datetime import datetime, timedelta, timezone

def list_upcoming_events(access_token, max_results=5):

    response = requests.get(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        headers={
            "Authorization": f"Bearer {access_token}"
        },
        params={
            "maxResults": max_results,
            "orderBy": "startTime",
            "singleEvents": "true",
            "timeMin": datetime.now(timezone.utc).isoformat()
        }
    )

    return response.json()

def create_calendar_event(
    title,
    meeting_date,
    access_token,
    attendees=[]
):

    try:
        start_dt = datetime.fromisoformat(meeting_date)
        end_date_time = (start_dt + timedelta(hours=1)).isoformat()
    except (TypeError, ValueError):
        end_date_time = meeting_date

    event = {
        "summary": title,
        "start": {
            "dateTime": meeting_date,
            "timeZone": "Asia/Kolkata"
        },
        "end": {
            "dateTime": end_date_time,
            "timeZone": "Asia/Kolkata"
        },

        "attendees": [
            {"email": email}
            for email in attendees
        ],

        "conferenceData": {
            "createRequest": {
                "requestId": title.replace(" ", "-")
            }
        }
    }

    response = requests.post(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events?conferenceDataVersion=1",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        },
        json=event
    )

    return response.json()