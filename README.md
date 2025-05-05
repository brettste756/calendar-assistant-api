# Calendar Assistant API

This backend powers a Custom GPT that:
- Checks your Outlook calendar availability
- Adds events to your Outlook calendar

## Features

- `/check-availability`: Uses GPT to parse scheduling queries and check your calendar
- `/create-event`: Adds events to your Outlook calendar with optional invitees

## Requirements

- Python 3.8+
- OpenAI API Key
- Microsoft Azure App with:
  - `Calendars.Read`
  - `Calendars.ReadWrite`
  - Admin consent granted

## API Endpoints

### POST /check-availability
```json
{
  "query": "Do I have time Thursday at 2 PM?"
}
```

**Response:**
```json
{
  "available": true,
  "summary": "You're free during that time."
}
```

---

### POST /create-event
```json
{
  "subject": "Team Meeting",
  "start_time": "2025-05-07T14:00:00Z",
  "end_time": "2025-05-07T15:00:00Z",
  "attendees": ["alex@example.com", "jane@example.com"]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Event created successfully."
}
```

## Deployment

1. Upload to GitHub
2. Deploy to [https://render.com](https://render.com)
3. Add environment variables:

- `OPENAI_API_KEY`
- `CLIENT_ID`
- `CLIENT_SECRET`
- `TENANT_ID`

**Start command:**
```
uvicorn main:app --host 0.0.0.0 --port 10000
```

## License

MIT