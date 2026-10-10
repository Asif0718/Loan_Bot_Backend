# Home Credit LAP Voice Agent Backend

Backend service for the Home Credit Loan Against Property (LAP) Voice Agent assessment project.
Handles Retell AI voice call integration and MongoDB storage of call history/post-call analysis.

## Setup

### 1. Create and activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Environment variables

Copy `.env.example` to `.env` and fill in the values:

```powershell
cp .env.example .env
```

Edit `.env` with your Retell API key, Agent ID, and MongoDB connection details.

### 4. Sync the assignment prompt to Retell

The complete, version-controlled agent prompt is in `app/prompts/lap_agent.txt`.
After setting `RETELL_API_KEY`, `RETELL_AGENT_ID`, and optionally
`PUBLIC_BASE_URL`, apply the prompt, webhook events, and post-call extraction
fields to the Retell agent:

```powershell
python scripts/sync_retell_agent.py
```

### 5. MongoDB setup

Ensure MongoDB is running and accessible via the `MONGODB_URI` environment variable.
The default database name is `home_credit_lap`.

## Local run

```powershell
uvicorn app.main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`.

## API Endpoints

### Health Check

- `GET /health` - Returns `{"status": "ok"}`

### Call Management

- `POST /api/calls/start` - Start a new Retell browser voice call
  - Request body: `{ "profile_id": "...", "agent_name": "Ananya" }`
  - Response: `{ "call_id": "...", "access_token": "..." }`

- `GET /api/calls` - Get recent calls from MongoDB
  - Query params: `page=1`, `limit=20`, `outcome=qualified`, `profile_id=...`
  - Response: `{ "items": [...], "page": 1, "limit": 20, "total": 42 }`

- `GET /api/calls/{retell_call_id}` - Get a single call record by Retell call ID
  - Response: Full call document
  - 404 if not found

### Profiles

- `POST /api/profiles` - Create a customer profile
  - Request body: `{ "customer_name": "Rahul Sharma", "language_to_speak": "English", "phone": "+91...", "dynamic_variables": {}, "metadata": {} }`
- `GET /api/profiles` - List profiles with `page` and `limit` pagination
- `GET /api/profiles/{profile_id}` - Get one profile
- `GET /api/profiles/{profile_id}/calls` - Get all calls for one profile

### Retell Webhooks

- `POST /webhooks/retell` - Receive Retell call events
  - Events: `call_started`, `transcript_updated`, `call_ended`, `call_analyzed`
  - Verifies the `x-retell-signature` header by default

## Retell Webhook Setup

Configure the webhook URL in your Retell dashboard:

```
POST https://your-backend-domain.com/webhooks/retell
```

The webhook idempotently upserts every supported event by Retell call ID:
- `call_started` - Creates the initial call record
- `transcript_updated` - Saves the latest live transcript
- `call_ended` - Saves the final transcript, recording, duration, and disconnect reason
- `call_analyzed` - Saves `call_analysis`, including summary, sentiment, success, and custom extraction data

In the Retell dashboard, enable all four events above. Set `VERIFY_RETELL_WEBHOOKS=false` only for isolated local tests; keep it enabled anywhere the endpoint is public.

## Project Structure

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── routes/
│   │   ├── health.py
│   │   ├── calls.py
│   │   └── webhooks.py
│   ├── services/
│   │   └── retell_service.py
│   ├── models/
│   │   └── call.py
│   └── schemas/
│       └── call.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Assumptions

- Run `python scripts/sync_retell_agent.py` after prompt/configuration changes
- The Retell Python SDK is used for all Retell API interactions
- MongoDB is accessible and the `calls` collection will be created automatically
- Webhook events may be retried, so idempotency is enforced via a unique MongoDB index on `retell_call_id`
