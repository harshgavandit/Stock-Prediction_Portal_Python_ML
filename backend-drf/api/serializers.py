import re

from rest_framework import serializers

TICKER_PATTERN = re.compile(r"^[A-Z0-9^][A-Z0-9.^=-]{0,19}$")


def normalize_ticker(value):
    if not isinstance(value, str):
        raise serializers.ValidationError("Each ticker must be a string.")
    value = value.strip().upper()
    if not TICKER_PATTERN.fullmatch(value):
        raise serializers.ValidationError("Use a valid ticker, for example AAPL or RELIANCE.NS.")
    return value


class StockPredictionSerializer(serializers.Serializer):
    ticker = serializers.CharField(max_length=20)

    def validate_ticker(self, value):
        return normalize_ticker(value)


class LivePriceSerializer(serializers.Serializer):
    tickers = serializers.ListField(child=serializers.CharField(max_length=20), max_length=10, allow_empty=True)

    def validate_tickers(self, values):
        return list(dict.fromkeys(normalize_ticker(value) for value in values))
