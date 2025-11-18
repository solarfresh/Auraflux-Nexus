from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class JWTCookieAuthentication(JWTAuthentication):
    """
    Looks only for the Access Token in the HTTP-only cookie.
    If the token is expired/invalid, it returns None/None to allow the
    view permission checks to return the 401 or 403, as expected.
    """
    def authenticate(self, request):
        # Look for the token in the designated cookie
        raw_token = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])

        if raw_token:
            try:
                # Attempt to validate the token
                validated_token = self.get_validated_token(raw_token)
                # Success: Return the user and validated token
                return self.get_user(validated_token), validated_token
            except (InvalidToken, TokenError):
                # IMPORTANT: If the token is invalid or expired,
                # we return None to indicate no authentication was provided.
                # This allows DRF to proceed to permission checks and ultimately
                # return a 401 if the view requires IsAuthenticated.
                return None

        # If no cookie token is found, return None
        # Do NOT fall back to super().authenticate(request) as it checks headers
        # which can confuse a cookie-only API.
        return None