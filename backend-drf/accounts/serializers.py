from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from api.serializers import normalize_ticker
from .models import UserPortfolio


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class ProfileSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True,
                                     min_length=8, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_password(self, value):
        if value:
            validate_password(value, self.instance)
        return value

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)
        if password:
            instance.set_password(password)
            instance.save()
        return instance


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPortfolio
        fields = ["tickers", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate_tickers(self, value):
        if not isinstance(value, list) or len(value) > 10:
            raise serializers.ValidationError("Provide a list of at most 10 ticker symbols.")
        tickers = [normalize_ticker(symbol) for symbol in value]
        if len(set(tickers)) != len(tickers):
            raise serializers.ValidationError("Ticker symbols must be unique.")
        return tickers
