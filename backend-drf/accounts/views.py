from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import UserPortfolio
from .serializers import PortfolioSerializer, ProfileSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class LoginView(TokenObtainPairView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class RefreshView(TokenRefreshView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"status": "Request was permitted", "user": {
            "username": request.user.username, "email": request.user.email,
        }})


class PortfolioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        portfolio, _ = UserPortfolio.objects.get_or_create(
            user=request.user, defaults={"tickers": ["RELIANCE.NS", "TCS.NS", "INFY.NS"]},
        )
        return Response(PortfolioSerializer(portfolio).data)

    def post(self, request):
        portfolio, _ = UserPortfolio.objects.get_or_create(user=request.user)
        serializer = PortfolioSerializer(portfolio, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"user": {"username": request.user.username, "email": request.user.email}})

    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"user": {
            "username": serializer.instance.username, "email": serializer.instance.email,
        }})
