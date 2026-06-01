# AI Complaint Categorizer Dashboard

AI-powered complaint categorization dashboard with a FastAPI backend.

## Backend Structure

```text
backend/
├── ai.py
├── database.py
├── main.py
├── models.py
├── schemas.py
└── test_api.py
```

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run backend server:

```bash
uvicorn backend.main:app --reload
```

## API Endpoints

- `POST /api/complaints`
  - Body: `{ "name": "string", "text": "string" }`
  - Returns created complaint with AI-generated `category`, `priority`, and `summary`.

- `GET /api/complaints`
  - Query params (optional): `category`, `status`, `priority`
  - Returns complaints for dashboard listing with filters.

- `GET /api/analytics`
  - Returns complaint summary counts: `total`, `high_priority`, `resolved`.

- `PATCH /api/complaints/{complaint_id}/resolve`
  - Marks a complaint as `resolved`.

## Frontend (starter)

A basic frontend starter is included in `frontend/`:

- `index.html` with complaint form + dashboard table
- filter controls for category/status/priority
- resolve action wired to `PATCH /api/complaints/{id}/resolve`
- analytics cards wired to `GET /api/analytics`

Open `/tmp/workspace/sirjanhere/ai-complaint-dashboard/frontend/index.html` in a browser while backend is running.

## Dependencies

Defined in `/tmp/workspace/sirjanhere/ai-complaint-dashboard/requirements.txt`:
- fastapi
- uvicorn
- sqlalchemy
- google-generativeai

## Notes

- Set `GEMINI_API_KEY` to use Gemini classification.
- If no API key is set, backend uses a fallback local categorization flow.
