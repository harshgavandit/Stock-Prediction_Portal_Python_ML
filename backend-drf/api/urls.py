from django.urls import path
from accounts import views as UserViews
from .views import HealthAPIView, StockPredictionAPIView, LivePriceAPIView


urlpatterns = [
    path('health/', HealthAPIView.as_view(), name='health'),
    path('register/', UserViews.RegisterView.as_view()),

    path('token/', UserViews.LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', UserViews.RefreshView.as_view(), name='token_refresh'),

    path('protected-view/', UserViews.ProtectedView.as_view()),
    path('profile/', UserViews.ProfileView.as_view()),

    # Prediction API
    path('predict/', StockPredictionAPIView.as_view(), name='stock_prediction'),
    
    # Portfolio Management
    path('portfolio/', UserViews.PortfolioView.as_view(), name='portfolio'),
    
    # Live Prices
    path('live-prices/', LivePriceAPIView.as_view(), name='live_prices')
]
