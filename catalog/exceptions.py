"""DRF exceptions with FastAPI-style error codes."""

from rest_framework.exceptions import APIException


class ItemNotFoundError(APIException):
    status_code = 404
    default_detail = "Item not found"
    default_code = "ITEM_NOT_FOUND"


class CategoryNotFoundError(APIException):
    status_code = 404
    default_detail = "Category not found"
    default_code = "CATEGORY_NOT_FOUND"


class CategoryInUseError(APIException):
    status_code = 409
    default_detail = "Category has items and cannot be deleted"
    default_code = "CATEGORY_IN_USE"


class CategoryNameExistsError(APIException):
    status_code = 409
    default_detail = "Category name already exists"
    default_code = "CATEGORY_NAME_EXISTS"

    def __init__(self, name: str) -> None:
        detail = f"Category name '{name}' already exists"
        super().__init__(detail=detail)


class UserEmailExistsError(APIException):
    status_code = 409
    default_detail = "User email already exists"
    default_code = "USER_EMAIL_EXISTS"

    def __init__(self, email: str) -> None:
        detail = f"User email '{email}' already exists"
        super().__init__(detail=detail)
