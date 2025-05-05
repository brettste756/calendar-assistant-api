from fastapi import FastAPI
from pydantic import BaseModel
import openai
import requests
from msal import ConfidentialClientApplication
import os
import json
from datetime import datetime

app = FastAPI()

# Load secrets from environment
openai.api_key = os.getenv("OPENAI_API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")

class QueryRequest(BaseModel):
    query: str

class EventRequest(BaseModel):
    subject: str
    start_time: str
    end_time: str
    attendees: list[str] = []

def get_graph_token():
    authority = f"https://login.microsoftonline.com/{TENANT_ID}"
    app = ConfidentialClientApplication(CLIENT_ID, authority=authority, client_credential=CLIENT_SECRET)
    token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return token.get("access_token")

def parse_time_with_gpt(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You convert scheduling questions into JSON with 'start_time' and 'end_time' in ISO 8601 UTC format."},
            {"role": "user", "content": f"Convert this to a 1-hour ISO 8601 time window in UTC: '{prompt}'. Return only JSON like {{'start_time': '...', 'end_time': '...'}}"}
        ],
        temperature=0
    )
    return response["choices"][0]["message"]["content"]

def check_calendar_events(token, start_time, end_time):
    url = "https://graph.microsoft.com/v1.0/me/calendarView"
    headers = {'Authorization': f'Bearer {token}', 'Prefer': 'outlook.timezone="UTC"'}
    params = {'startDateTime': start_time, 'endDateTime': end_time}
    res = requests.get(url, headers=headers, params=params)
    return res.json().get("value", []) if res.status_code == 200 else []

@app.post("/check-availability")
async def check_availability(req: QueryRequest):
    parsed = parse_time_with_gpt(req.query)

    try:
        time_data = json.loads(parsed.replace("'", '"'))  # Handle single quotes if needed
        start_time = time_data["start_time"]
        end_time = time_data["end_time"]
    except Exception as e:
        return {"available": False, "summary": f"Time parsing failed: {str(e)}"}

    token = get_graph_token()
    events = check_calendar_events(token, start_time, end_time)

    if not events:
        return {"available": True, "summary": "You're free during that time."}
    else:
        summary = "You have the following event(s): " + "; ".join(
            f"{e['subject']} from {e['start']['dateTime']} to {e['end']['dateTime']}" for e in events
        )
        return {"available": False, "summary": summary}

@app.post("/create-event")
async def create_event(event: EventRequest):
    token = get_graph_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    event_data = {
        "subject": event.subject,
        "start": {
            "dateTime": event.start_time,
            "timeZone": "UTC"
        },
        "end": {
            "dateTime": event.end_time,
            "timeZone": "UTC"
        },
        "attendees": [
            {
                "emailAddress": {"address": email, "name": email.split('@')[0]},
                "type": "required"
            } for email in event.attendees
        ]
    }

    response = requests.post("https://graph.microsoft.com/v1.0/me/events", headers=headers, json=event_data)

    if response.status_code == 201:
        return {"success": True, "message": "Event created successfully."}
    else:
        return {"success": False, "error": response.text}