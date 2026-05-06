from django.db import models
from django.contrib.auth.models import User

class UserPortfolio(models.Model):
    """Store user watchlist and portfolio preferences."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    tickers = models.JSONField(default=list)  # List of ticker symbols
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Portfolio'
        verbose_name_plural = 'User Portfolios'

    def __str__(self):
        return f"{self.user.username}'s Portfolio"
