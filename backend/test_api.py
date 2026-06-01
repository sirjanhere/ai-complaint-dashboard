import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.database import Base, SessionLocal, engine
from backend.main import app
from backend.models import Complaint


class ComplaintApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

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

        create_response = self.client.post(
            "/api/complaints",
            json={"name": "Asha", "text": "Room fan not working, urgent"},
        )
        self.assertEqual(create_response.status_code, 200)
        created = create_response.json()
        self.assertEqual(created["name"], "Asha")
        self.assertEqual(created["status"], "pending")
        self.assertEqual(created["category"], "Hostel")
        self.assertEqual(created["priority"], "High")

        list_response = self.client.get("/api/complaints")
        self.assertEqual(list_response.status_code, 200)
        complaints = list_response.json()
        self.assertEqual(len(complaints), 1)
        self.assertEqual(complaints[0]["id"], created["id"])

    @patch("backend.main.categorize_complaint")
    def test_rejects_whitespace_complaint_text(self, mock_categorize) -> None:
        create_response = self.client.post(
            "/api/complaints",
            json={"name": "Asha", "text": "   "},
        )
        self.assertEqual(create_response.status_code, 422)
        mock_categorize.assert_not_called()

    @patch("backend.main.categorize_complaint")
    def test_resolve_flow(self, mock_categorize) -> None:
        mock_categorize.return_value = {
            "category": "WiFi",
            "priority": "Medium",
            "summary": "WiFi drops frequently.",
        }
        created = self.client.post(
            "/api/complaints",
            json={"name": "Ravi", "text": "WiFi drops frequently in hostel block B"},
        ).json()

        resolve_response = self.client.patch(f"/api/complaints/{created['id']}/resolve")
        self.assertEqual(resolve_response.status_code, 200)
        self.assertEqual(resolve_response.json()["status"], "resolved")

    @patch("backend.main.categorize_complaint")
    def test_filters_by_category_status_and_priority(self, mock_categorize) -> None:
        mock_categorize.side_effect = [
            {"category": "Hostel", "priority": "High", "summary": "Hostel issue"},
            {"category": "WiFi", "priority": "Low", "summary": "WiFi issue"},
            {"category": "Hostel", "priority": "Low", "summary": "Another hostel issue"},
        ]

        first = self.client.post("/api/complaints", json={"name": "A", "text": "hostel urgent"}).json()
        self.client.post("/api/complaints", json={"name": "B", "text": "wifi slow"})
        self.client.post("/api/complaints", json={"name": "C", "text": "hostel gate light"})
        self.client.patch(f"/api/complaints/{first['id']}/resolve")

        by_category = self.client.get("/api/complaints", params={"category": "Hostel"})
        self.assertEqual(by_category.status_code, 200)
        self.assertEqual(len(by_category.json()), 2)

        by_status = self.client.get("/api/complaints", params={"status": "resolved"})
        self.assertEqual(by_status.status_code, 200)
        self.assertEqual(len(by_status.json()), 1)

        by_priority = self.client.get("/api/complaints", params={"priority": "Low"})
        self.assertEqual(by_priority.status_code, 200)
        self.assertEqual(len(by_priority.json()), 2)

        combined = self.client.get(
            "/api/complaints",
            params={"category": "Hostel", "status": "resolved", "priority": "High"},
        )
        self.assertEqual(combined.status_code, 200)
        self.assertEqual(len(combined.json()), 1)

    @patch("backend.main.categorize_complaint")
    def test_analytics_endpoint(self, mock_categorize) -> None:
        mock_categorize.side_effect = [
            {"category": "Hostel", "priority": "High", "summary": "Hostel issue"},
            {"category": "Classroom", "priority": "Medium", "summary": "Projector issue"},
            {"category": "WiFi", "priority": "High", "summary": "Network issue"},
        ]

        first = self.client.post("/api/complaints", json={"name": "A", "text": "hostel urgent"}).json()
        self.client.post("/api/complaints", json={"name": "B", "text": "projector not working"})
        self.client.post("/api/complaints", json={"name": "C", "text": "wifi down"})
        self.client.patch(f"/api/complaints/{first['id']}/resolve")

        analytics_response = self.client.get("/api/analytics")
        self.assertEqual(analytics_response.status_code, 200)
        payload = analytics_response.json()
        self.assertEqual(payload["total"], 3)
        self.assertEqual(payload["high_priority"], 2)
        self.assertEqual(payload["resolved"], 1)


if __name__ == "__main__":
    unittest.main()
