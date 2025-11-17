from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings


class JWTCookieAuthentication(JWTAuthentication):
    """
    Looks for the Access Token in the HTTP-only cookie defined by
    SIMPLE_JWT['AUTH_COOKIE'].
    """
    def authenticate(self, request):
        # 1. Check for token in the designated cookie
        raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])

        if raw_token:
            # If found, retrieve the user and token information
            validated_token = self.get_validated_token(raw_token)
            return self.get_user(validated_token), validated_token

        # Fallback to default header authentication if the cookie isn't present
        # (optional, but good practice for API clients)
        return super().authenticate(request)
