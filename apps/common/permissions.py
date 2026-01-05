from rest_framework.permissions import BasePermission, SAFE_METHODS


class ReadOnlyOrAuthenticated(BasePermission):
   
    def has_permission(self, request, view):
        # Allow read-only methods for everyone
        if request.method in SAFE_METHODS:
            return True

        # Write permissions only for authenticated users
        return request.user and request.user.is_authenticated
