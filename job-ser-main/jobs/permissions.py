import secrets

from django.conf import settings
from rest_framework.permissions import BasePermission


class HasInternalAPIToken(BasePermission):
    message = "Missing or invalid internal API token."

    def has_permission(self, request, view):
        token = request.headers.get("X-Internal-Token", "")
        expected = settings.INTERNAL_API_TOKEN
        return bool(expected) and secrets.compare_digest(token, expected)
