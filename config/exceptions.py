"""Custom DRF exception handler matching FastAPI-101 error shape."""

from rest_framework.exceptions import APIException, Throttled, ValidationError
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """Return { detail, code } for application errors; 422 for validation."""
    response = exception_handler(exc, context)
    if response is None:
        return response

    if isinstance(exc, ValidationError):
        response.status_code = 422
        if isinstance(response.data, dict):
            response.data = {"detail": response.data}
        return response

    if isinstance(exc, Throttled):
        response.data = {"detail": "Rate limit exceeded", "code": "RATE_LIMIT_EXCEEDED"}
        return response

    if isinstance(exc, APIException):
        detail = response.data.get("detail") if isinstance(response.data, dict) else str(exc)
        code = getattr(exc, "default_code", "ERROR")
        if isinstance(code, str) and code.islower() and "_" not in code:
            code = code.upper()
        response.data = {"detail": detail, "code": code}

    return response
