"""Skip/limit pagination matching FastAPI-101 list responses."""

from rest_framework.pagination import BasePagination
from rest_framework.response import Response


class SkipLimitPagination(BasePagination):
    """Paginate with skip and limit query params (FastAPI-101 shape)."""

    default_limit = 10
    max_limit = 100

    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        try:
            self.skip = max(0, int(request.query_params.get("skip", 0)))
        except (TypeError, ValueError):
            self.skip = 0
        try:
            self.limit = int(request.query_params.get("limit", self.default_limit))
        except (TypeError, ValueError):
            self.limit = self.default_limit
        if self.limit < 1 or self.limit > self.max_limit:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"limit": ["limit must be between 1 and 100"]})
        if self.skip < 0:
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"skip": ["skip must be >= 0"]})

        self.total = queryset.count()
        return list(queryset[self.skip : self.skip + self.limit])

    def get_paginated_response(self, data):
        return Response(
            {
                "items": data,
                "total": self.total,
                "skip": self.skip,
                "limit": self.limit,
            }
        )
