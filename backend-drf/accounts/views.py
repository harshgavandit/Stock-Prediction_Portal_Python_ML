from django.shortcuts import render
from .serializers import UserSerializer, PortfolioSerializer, ProfileSerializer
from .models import UserPortfolio
from rest_framework import generics
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        response = {
            'status': 'Request was permitted',
            'user': {
                'username': request.user.username,
                'email': request.user.email,
            }
        }
        return Response(response)


class PortfolioView(APIView):
    """Manage user watchlist/portfolio."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Retrieve user portfolio."""
        try:
            portfolio = request.user.portfolio
            serializer = PortfolioSerializer(portfolio)
            return Response(serializer.data)
        except UserPortfolio.DoesNotExist:
            # Create default portfolio if doesn't exist
            portfolio = UserPortfolio.objects.create(
                user=request.user,
                tickers=['RELIANCE.NS', 'TCS.NS', 'INFY.NS']
            )
            serializer = PortfolioSerializer(portfolio)
            return Response(serializer.data)

    def post(self, request):
        """Update user portfolio tickers."""
        try:
            portfolio = request.user.portfolio
        except UserPortfolio.DoesNotExist:
            portfolio = UserPortfolio.objects.create(user=request.user)
        
        serializer = PortfolioSerializer(portfolio, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'user': {
                'username': request.user.username,
                'email': request.user.email,
            }
        })

    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'user': {
                    'username': serializer.instance.username,
                    'email': serializer.instance.email,
                }
            })
        return Response(serializer.errors, status=400)
