from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APITestCase


class AccountFlowTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.password = "Synthetic-only-Password!712"

    def register_and_login(self, username="verificationuser"):
        response = self.client.post("/api/v1/register/", {
            "username": username, "email": username + "@example.invalid", "password": self.password,
        })
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.data)
        token = self.client.post("/api/v1/token/", {"username": username, "password": self.password})
        self.assertEqual(token.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token.data["access"])
        return token.data

    def test_registration_login_profile_and_refresh(self):
        tokens = self.register_and_login()
        self.assertTrue(User.objects.get(username="verificationuser").check_password(self.password))
        self.assertEqual(self.client.get("/api/v1/protected-view/").status_code, 200)
        updated = self.client.patch("/api/v1/profile/", {"email": "updated@example.invalid"})
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["user"]["email"], "updated@example.invalid")
        refreshed = self.client.post("/api/v1/token/refresh/", {"refresh": tokens["refresh"]})
        self.assertEqual(refreshed.status_code, 200)
        self.assertIn("access", refreshed.data)

    def test_weak_password_and_duplicate_username_are_rejected(self):
        self.assertEqual(self.client.post("/api/v1/register/", {
            "username": "test", "email": "test@example.invalid", "password": "password",
        }).status_code, 400)
        self.register_and_login()
        self.assertEqual(self.client.post("/api/v1/register/", {
            "username": "verificationuser", "email": "duplicate@example.invalid", "password": self.password,
        }).status_code, 400)

    def test_watchlists_are_persistent_isolated_and_allow_empty(self):
        self.register_and_login()
        self.assertEqual(self.client.get("/api/v1/portfolio/").status_code, 200)
        response = self.client.post("/api/v1/portfolio/", {"tickers": [" aapl ", "RELIANCE.NS"]}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/portfolio/").data["tickers"], ["AAPL", "RELIANCE.NS"])
        first = User.objects.get(username="verificationuser")
        second = User.objects.create_user("seconduser", password=self.password)
        self.client.force_authenticate(second)
        self.assertNotEqual(self.client.get("/api/v1/portfolio/").data["tickers"], first.portfolio.tickers)
        self.client.force_authenticate(first)
        self.assertEqual(self.client.post("/api/v1/portfolio/", {"tickers": []}, format="json").status_code, 200)
        self.assertEqual(self.client.get("/api/v1/portfolio/").data["tickers"], [])

    def test_watchlist_validation(self):
        self.register_and_login()
        for tickers in (["A"] * 11, ["AAPL", "aapl"], ["../etc"], "AAPL", [123]):
            self.assertEqual(self.client.post("/api/v1/portfolio/", {"tickers": tickers}, format="json").status_code, 400)

    def test_private_endpoints_reject_anonymous_requests(self):
        for endpoint in ("profile", "portfolio", "protected-view"):
            self.assertEqual(self.client.get(f"/api/v1/{endpoint}/").status_code, 401)
