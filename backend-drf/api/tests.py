import base64
from pathlib import Path
from unittest.mock import patch

import numpy as np
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from .inference import predict
from .market import MarketDataError


class ModelParityTests(SimpleTestCase):
    def test_numpy_inference_matches_original_tensorflow_reference(self):
        with np.load(Path(__file__).with_name("model_reference.npz")) as reference:
            np.testing.assert_allclose(predict(reference["inputs"]), reference["expected"], rtol=2e-5, atol=2e-6)

    def test_bad_shape_and_nonfinite_inputs_are_rejected(self):
        for value in [np.zeros((1, 20, 1)), np.full((1, 100, 1), np.nan)]:
            with self.assertRaises(ValueError):
                predict(value)


class PredictionTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user("modeltester", password="Synthetic-only-Password!712")
        self.client.force_authenticate(self.user)

    def test_prediction_requires_authentication(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post("/api/v1/predict/", {"ticker": "AAPL"}).status_code, 401)

    def test_invalid_ticker_never_calls_provider(self):
        with patch("api.views.history") as fetch:
            response = self.client.post("/api/v1/predict/", {"ticker": "../../secret"})
        self.assertEqual(response.status_code, 400)
        fetch.assert_not_called()

    def test_provider_failure_returns_an_actionable_error(self):
        with patch("api.views.history", side_effect=MarketDataError("Provider unavailable")):
            response = self.client.post("/api/v1/predict/", {"ticker": "AAPL"})
        self.assertEqual(response.status_code, 503)
        self.assertIn("error", response.data)

    def test_short_history_is_rejected(self):
        data = {"close": list(range(1, 101))}
        with patch("api.views.history", return_value=data):
            response = self.client.post("/api/v1/predict/", {"ticker": "AAPL"})
        self.assertEqual(response.status_code, 422)

    def test_real_model_generates_finite_metrics_and_self_contained_pngs(self):
        closes = (100 + np.arange(360) * 0.1 + np.sin(np.arange(360) / 10)).tolist()
        data = {"close": closes, "dates": ["2026-01-01"] * 360, "meta": {"currency": "USD"}, "source": "Synthetic test fixture"}
        with patch("api.views.history", return_value=data):
            response = self.client.post("/api/v1/predict/", {"ticker": "aapl"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["ticker"], "AAPL")
        self.assertTrue(np.isfinite([response.data[key] for key in ("mse", "rmse", "r2", "next_close")]).all())
        for key in ("plot_img", "plot_100_dma", "plot_200_dma", "plot_prediction"):
            prefix, encoded = response.data[key].split(",", 1)
            self.assertEqual(prefix, "data:image/png;base64")
            self.assertTrue(base64.b64decode(encoded).startswith(b"\x89PNG"))
        self.assertEqual(response.data["evaluation_rows"], 109)

    def test_live_prices_are_validated_and_empty_watchlist_is_supported(self):
        self.assertEqual(self.client.post("/api/v1/live-prices/", {"tickers": ["A"] * 11}, format="json").status_code, 400)
        response = self.client.post("/api/v1/live-prices/", {"tickers": []}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["prices"], {})

    def test_health_checks_model_and_database(self):
        self.client.force_authenticate(None)
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["model"], "ready")
