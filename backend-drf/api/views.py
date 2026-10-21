import logging
import threading

import numpy as np
from django.core.cache import cache
from django.db import connection
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .inference import predict, weights
from .market import MarketDataError, history, prices
from .serializers import LivePriceSerializer, StockPredictionSerializer
from .utils import plot_data_uri

logger = logging.getLogger(__name__)
plot_lock = threading.Lock()


class HealthAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            weights()
            return Response({"status": "ok", "database": "connected", "model": "ready"})
        except Exception:
            logger.exception("Readiness check failed")
            return Response({"status": "unavailable"}, status=503)


def _moving_average(values, window):
    if len(values) < window:
        return np.full(len(values), np.nan)
    return np.concatenate([np.full(window - 1, np.nan),
                           np.convolve(values, np.ones(window) / window, mode="valid")])


def _chart(title, series):
    # Matplotlib's renderer is not thread-safe. Figures never touch shared pyplot state.
    from matplotlib.figure import Figure
    with plot_lock:
        figure = Figure(figsize=(10, 4))
        axis = figure.subplots()
        for values, label, color in series:
            axis.plot(values, label=label, color=color, linewidth=1.2)
        axis.set(title=title, xlabel="Trading sessions", ylabel="Closing price")
        axis.legend()
        axis.grid(alpha=0.15)
        figure.tight_layout()
        return plot_data_uri(figure)


class StockPredictionAPIView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "prediction"

    def post(self, request):
        serializer = StockPredictionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ticker = serializer.validated_data["ticker"]
        cache_key = f"prediction:v1:{ticker}"
        cached = cache.get(cache_key)
        if cached is not None:
            return Response(cached)
        try:
            data = history(ticker)
        except MarketDataError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        closes = np.asarray(data["close"], dtype=np.float64)
        split = int(len(closes) * 0.7)
        if split < 100 or len(closes) - split < 2:
            return Response({"error": "At least 145 daily closing prices are needed for this model."}, status=422)
        # Fit on the first 70% only: evaluation prices must not influence scaling.
        lower = float(closes[:split].min())
        scale = float(closes[:split].max() - lower) or 1.0
        scaled = ((closes - lower) / scale).astype(np.float32)
        windows = np.lib.stride_tricks.sliding_window_view(scaled, 100)
        sequences = windows[split - 100:-1, :, None]
        actual = closes[split:]
        try:
            estimates = predict(sequences).ravel().astype(np.float64) * scale + lower
            next_close = float(predict(scaled[-100:].reshape(1, 100, 1))[0, 0]) * scale + lower
            residual = actual - estimates
            mse = float(np.mean(residual ** 2))
            variance = float(np.sum((actual - actual.mean()) ** 2))
            r2 = float(1 - np.sum(residual ** 2) / variance) if variance else 0.0
            if not np.isfinite([mse, r2, next_close]).all():
                raise ValueError("Non-finite model result")
            average100 = _moving_average(closes, 100)
            average200 = _moving_average(closes, 200)
            result = {
                "status": "success", "ticker": ticker,
                "plot_img": _chart(f"{ticker}: closing prices", [(closes, "Close", "#2563eb")]),
                "plot_100_dma": _chart(f"{ticker}: 100-day moving average",
                    [(closes, "Close", "#2563eb"), (average100, "100 DMA", "#dc2626")]),
                "plot_200_dma": _chart(f"{ticker}: moving averages",
                    [(closes, "Close", "#2563eb"), (average100, "100 DMA", "#dc2626"),
                     (average200, "200 DMA", "#16a34a")]),
                "plot_prediction": _chart(f"{ticker}: historical model comparison",
                    [(actual, "Actual close", "#2563eb"), (estimates, "LSTM estimate", "#dc2626")]),
                "mse": mse, "rmse": float(np.sqrt(mse)), "r2": r2,
                "next_close": next_close, "as_of": data["dates"][-1],
                "currency": data["meta"].get("currency"), "source": data["source"],
                "history_rows": len(closes), "evaluation_rows": len(actual),
                "evaluation": "Historical comparison using the existing pretrained model; R-squared is not a probability.",
            }
            cache.set(cache_key, result, 900)
            return Response(result)
        except Exception:
            logger.exception("Prediction failed for %s", ticker)
            return Response({"error": "The prediction could not be generated. Please try again shortly."}, status=503)


class LivePriceAPIView(APIView):
    def post(self, request):
        serializer = LivePriceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"status": "success", "prices": prices(serializer.validated_data["tickers"])})
