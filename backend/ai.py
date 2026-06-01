import json
import os
import re
from typing import Any

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover
    genai = None


CATEGORIES = ["WiFi", "Hostel", "Electricity", "Classroom", "Other"]
PRIORITIES = ["Low", "Medium", "High"]


def _normalize_category(value: Any) -> str:
    text = str(value or "").strip().lower()
    mapping = {
        "wifi": "WiFi",
        "wi-fi": "WiFi",
        "internet": "WiFi",
        "hostel": "Hostel",
        "room": "Hostel",
        "electricity": "Electricity",
        "power": "Electricity",
        "classroom": "Classroom",
        "class": "Classroom",
        "other": "Other",
    }
    for key, normalized in mapping.items():
        if key in text:
            return normalized
    return "Other"


def _normalize_priority(value: Any) -> str:
    text = str(value or "").strip().lower()
    if "high" in text or "urgent" in text:
        return "High"
    if "low" in text:
        return "Low"
    return "Medium"


def _build_summary(text: str) -> str:
    cleaned = " ".join((text or "").strip().split())
    if not cleaned:
        return "No complaint details provided."
    return cleaned[:120] + ("..." if len(cleaned) > 120 else "")


def _fallback_categorization(complaint_text: str) -> dict[str, str]:
    lowered = (complaint_text or "").lower()

    if any(word in lowered for word in ["wifi", "wi-fi", "internet", "network"]):
        category = "WiFi"
    elif any(word in lowered for word in ["hostel", "room", "mess", "dorm"]):
        category = "Hostel"
    elif any(word in lowered for word in ["electricity", "power", "voltage", "light"]):
        category = "Electricity"
    elif any(word in lowered for word in ["class", "classroom", "lab", "projector"]):
        category = "Classroom"
    else:
        category = "Other"

    if any(word in lowered for word in ["urgent", "immediately", "danger", "critical", "not working"]):
        priority = "High"
    elif any(word in lowered for word in ["minor", "whenever", "later"]):
        priority = "Low"
    else:
        priority = "Medium"

    return {
        "category": category,
        "priority": priority,
        "summary": _build_summary(complaint_text),
    }


def _parse_response(raw_text: str, complaint_text: str) -> dict[str, str]:
    if raw_text:
        json_match = re.search(r"\{[\s\S]*\}", raw_text)
        if json_match:
            try:
                payload = json.loads(json_match.group(0))
                return {
                    "category": _normalize_category(payload.get("category")),
                    "priority": _normalize_priority(payload.get("priority")),
                    "summary": str(payload.get("summary") or _build_summary(complaint_text)).strip(),
                }
            except json.JSONDecodeError:
                pass

        category_match = re.search(r"category\s*:\s*(.+)", raw_text, re.IGNORECASE)
        priority_match = re.search(r"priority\s*:\s*(.+)", raw_text, re.IGNORECASE)
        summary_match = re.search(r"summary\s*:\s*(.+)", raw_text, re.IGNORECASE)
        if category_match or priority_match or summary_match:
            return {
                "category": _normalize_category(category_match.group(1) if category_match else "Other"),
                "priority": _normalize_priority(priority_match.group(1) if priority_match else "Medium"),
                "summary": (summary_match.group(1).strip() if summary_match else _build_summary(complaint_text)),
            }

    return _fallback_categorization(complaint_text)


def categorize_complaint(complaint_text: str) -> dict[str, str]:
    complaint_text = (complaint_text or "").strip()
    if not complaint_text:
        return {
            "category": "Other",
            "priority": "Low",
            "summary": "No complaint details provided.",
        }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or genai is None:
        return _fallback_categorization(complaint_text)

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = (
            "Categorize the complaint and return only JSON with keys: "
            "category, priority, summary. "
            "Allowed categories: WiFi, Hostel, Electricity, Classroom, Other. "
            "Allowed priorities: Low, Medium, High.\n\n"
            f"Complaint: {complaint_text}"
        )
        response = model.generate_content(prompt)
        raw_text = getattr(response, "text", "") or ""
        return _parse_response(raw_text, complaint_text)
    except Exception:
        return _fallback_categorization(complaint_text)
