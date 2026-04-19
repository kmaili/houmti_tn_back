from rest_framework.permissions import BasePermission

class IsArtistan(BasePermission):
    message = "Only artistan can access this endpoint"

    def has_permission(self, request, *args, **kwargs):
        user = request.user

        if not user or not user.is_authenticated:
            return False
        return hasattr(user, "artist")

class IsClient(BasePermission):
    message = "Only clients can access this endpoint"

    def has_permission(self, request, *args, **kwargs):
        user = request.user

        if not user or not user.is_authenticated:
            return False
        return hasattr(user, "client")