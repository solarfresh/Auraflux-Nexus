from django.urls import path
from .views import LoginView, RefreshTokenView


urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', RefreshTokenView.as_view(), name='token_refresh'),
    # ... other user-related endpoints
]