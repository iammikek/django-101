"""Root and health check views."""

from django.db import DatabaseError
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.services import ItemService


class RootResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class HealthResponseSerializer(serializers.Serializer):
    status = serializers.CharField()
    database = serializers.CharField()


@extend_schema(responses={200: RootResponseSerializer})
class RootView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"message": "Hello from Django!"})


@extend_schema(responses={200: HealthResponseSerializer})
class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        try:
            ItemService.check_database()
        except DatabaseError:
            return Response({"detail": "Database unavailable"}, status=503)
        return Response({"status": "ok", "database": "connected"})
