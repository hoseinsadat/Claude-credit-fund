from rest_framework.permissions import BasePermission


class IsPortalUser(BasePermission):
    """Only allow portal users (CLIENT_USER role)."""

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.is_portal_user
            and request.user.role == 'CLIENT_USER'
        )


class IsOwnerOfClient(BasePermission):
    """Ensure user can only access their linked client's data."""

    def has_object_permission(self, request, view, obj):
        client = getattr(obj, 'client', None)
        if client is None:
            return False
        return client.portal_user == request.user
