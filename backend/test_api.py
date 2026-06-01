import unittest
from unittest.mock import patch

from pydantic import ValidationError

from backend.database import Base, SessionLocal, engine
from backend.main import complaint_analytics, create_complaint, list_complaints, resolve_complaint
from backend.models import Complaint
from backend.schemas import ComplaintCategory, ComplaintCreate, ComplaintPriority, ComplaintStatus


class ComplaintApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(bind=engine)

    def setUp(self) -> None:
        with SessionLocal() as db:
            db.query(Complaint).delete()
            db.commit()

    @patch("backend.main.categorize_complaint")
    def test_create_and_list_complaint(self, mock_categorize) -> None:
        mock_categorize.return_value = {
            "category": "Hostel",
            "priority": "High",
            "summary": "Room fan not working.",
        }

        with SessionLocal() as db:
            created = create_complaint(
                ComplaintCreate(name="Asha", text="Room fan not working, urgent"),
                db=db,
            ).model_dump(mode="json")

        self.assertEqual(created["name"], "Asha")
        self.assertEqual(created["status"], "pending")
        self.assertEqual(created["category"], "Hostel")
        self.assertEqual(created["priority"], "High")

        with SessionLocal() as db:
            complaints = [item.model_dump(mode="json") for item in list_complaints(db=db)]
        self.assertEqual(len(complaints), 1)
        self.assertEqual(complaints[0]["id"], created["id"])

    def test_rejects_whitespace_complaint_text(self) -> None:
        with self.assertRaises(ValidationError):
            ComplaintCreate(name="Asha", text="   ")

    @patch("backend.main.categorize_complaint")
    def test_resolve_flow(self, mock_categorize) -> None:
        mock_categorize.return_value = {
            "category": "WiFi",
            "priority": "Medium",
            "summary": "WiFi drops frequently.",
        }
        with SessionLocal() as db:
            created = create_complaint(
                ComplaintCreate(name="Ravi", text="WiFi drops frequently in hostel block B"),
                db=db,
            )
            resolved = resolve_complaint(created.id, db=db).model_dump(mode="json")
        self.assertEqual(resolved["status"], "resolved")

    @patch("backend.main.categorize_complaint")
    def test_filters_by_category_status_and_priority(self, mock_categorize) -> None:
        mock_categorize.side_effect = [
            {"category": "Hostel", "priority": "High", "summary": "Hostel issue"},
            {"category": "WiFi", "priority": "Low", "summary": "WiFi issue"},
            {"category": "Hostel", "priority": "Low", "summary": "Another hostel issue"},
        ]

        with SessionLocal() as db:
            first = create_complaint(ComplaintCreate(name="A", text="hostel urgent"), db=db)
            create_complaint(ComplaintCreate(name="B", text="wifi slow"), db=db)
            create_complaint(ComplaintCreate(name="C", text="hostel gate light"), db=db)
            resolve_complaint(first.id, db=db)

            by_category = list_complaints(category=ComplaintCategory.HOSTEL, db=db)
            self.assertEqual(len(by_category), 2)

            by_status = list_complaints(status=ComplaintStatus.RESOLVED, db=db)
            self.assertEqual(len(by_status), 1)

            by_priority = list_complaints(priority=ComplaintPriority.LOW, db=db)
            self.assertEqual(len(by_priority), 2)

            combined = list_complaints(
                category=ComplaintCategory.HOSTEL,
                status=ComplaintStatus.RESOLVED,
                priority=ComplaintPriority.HIGH,
                db=db,
            )
            self.assertEqual(len(combined), 1)

    @patch("backend.main.categorize_complaint")
    def test_analytics_endpoint(self, mock_categorize) -> None:
        mock_categorize.side_effect = [
            {"category": "Hostel", "priority": "High", "summary": "Hostel issue"},
            {"category": "Classroom", "priority": "Medium", "summary": "Projector issue"},
            {"category": "WiFi", "priority": "High", "summary": "Network issue"},
        ]

        with SessionLocal() as db:
            first = create_complaint(ComplaintCreate(name="A", text="hostel urgent"), db=db)
            create_complaint(ComplaintCreate(name="B", text="projector not working"), db=db)
            create_complaint(ComplaintCreate(name="C", text="wifi down"), db=db)
            resolve_complaint(first.id, db=db)
            payload = complaint_analytics(db=db).model_dump()
        self.assertEqual(payload["total"], 3)
        self.assertEqual(payload["high_priority"], 2)
        self.assertEqual(payload["resolved"], 1)


if __name__ == "__main__":
    unittest.main()
