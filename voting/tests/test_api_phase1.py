# voting/tests/test_api_phase1.py

from datetime import timedelta
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient

from voting.models import Election, Candidate

User = get_user_model()


class Phase1APITests(APITestCase):
    def setUp(self):
        # Owner (creator of election)
        self.owner = User.objects.create_user(username="owner", password="ownerpass")

        # One open election
        self.election = Election.objects.create(
            title="API Test Election",
            description="",
            allow_anonymous=True,          # guests allowed (for the anon test)
            allow_vote_comments=False,     # no comment required
            show_results_immediately=False,
            start_date=timezone.now() - timedelta(hours=1),
            end_date=timezone.now() + timedelta(hours=1),
            creator=self.owner,
            is_active=True,
            is_reviewed=True,
        )
        self.cand = Candidate.objects.create(
            election=self.election,
            name="Candidate A",
            party="",
            is_active=True,
            is_reviewed=True,
        )

        # Authenticated client (force-auth to avoid any header/JWT parsing issues)
        self.user = User.objects.create_user(
            username="alice", email="a@example.com", password="password123"
        )
        self.auth_client = APIClient()
        self.auth_client.force_authenticate(user=self.user)

        # Anonymous client
        self.anon_client = APIClient()

    def test_vote_once_then_conflict_authenticated(self):
        """Logged-in users can vote once; second vote is 409 even if allow_anonymous=True."""
        payload = {
            "election": self.election.id,
            "candidate": self.cand.id,
        }
        r1 = self.auth_client.post("/api/v1/votes/", payload, format="json")
        self.assertEqual(r1.status_code, 201, r1.content)

        r2 = self.auth_client.post("/api/v1/votes/", payload, format="json")
        self.assertEqual(r2.status_code, 409, r2.content)

    def test_vote_once_then_conflict_anonymous_with_fingerprint(self):
        """Guests must include a device_fingerprint; duplicate fingerprint gets 409."""
        payload = {
            "election": self.election.id,
            "candidate": self.cand.id,
            "device_fingerprint": "test-device-123",
        }
        r1 = self.anon_client.post("/api/v1/votes/", payload, format="json")
        self.assertEqual(r1.status_code, 201, r1.content)

        r2 = self.anon_client.post("/api/v1/votes/", payload, format="json")
        self.assertEqual(r2.status_code, 409, r2.content)
