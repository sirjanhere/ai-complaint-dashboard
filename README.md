# AI Complaint Categorizer Dashboard

AI-powered complaint categorization dashboard with a FastAPI backend.

## Backend Structure

```text
backend/
├── ai.py
├── database.py
├── main.py
└── models.py
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
  - Returns all complaints for dashboard listing.

- `PATCH /api/complaints/{complaint_id}/resolve`
  - Marks a complaint as `resolved`.

## Dependencies

Defined in `/tmp/workspace/sirjanhere/ai-complaint-dashboard/requirements.txt`:
- fastapi
- uvicorn
- sqlalchemy
- google-generativeai

## Notes

- Set `GEMINI_API_KEY` to use Gemini classification.
- If no API key is set, backend uses a fallback local categorization flow.
