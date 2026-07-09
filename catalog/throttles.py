"""IP-based throttles matching FastAPI-101 rate limits."""

from rest_framework.throttling import AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    scope = "auth"


class WriteRateThrottle(AnonRateThrottle):
    scope = "writes"
