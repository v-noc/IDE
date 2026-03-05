import httpx


class JWTAuth(httpx.Auth):
    """Class for JWT Authentication in requests."""

    def __init__(self, token):
        self._token = token

    def __call__(self, request):
        request.headers["Authorization"] = f"Bearer {self._token}"
        yield request


class APITokenAuth(httpx.Auth):
    """Class for API Token Authentication in requests."""

    def __init__(self, token):
        self._token = token

    def __call__(self, request):
        request.headers["Authorization"] = f"Token {self._token}"
        yield request
