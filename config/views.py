"""Root and health check views."""

from django.db import DatabaseError
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.services import ItemService


class RootView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"message": "Hello from Django!"})


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        try:
            ItemService.check_database()
        except DatabaseError:
            return Response({"detail": "Database unavailable"}, status=503)
        return Response({"status": "ok", "database": "connected"})
