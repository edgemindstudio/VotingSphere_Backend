# voting/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.permissions import IsAdminUser as DRFIsAdminUser

class IsAdminUser(DRFIsAdminUser):
    """Alias DRF's built-in IsAdminUser to match your import name."""
    pass

class IsAdminOrModerator(BasePermission):
    """
    Allow staff/superusers or users in a 'moderator' group.
    Adjust group names if you use something else.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        # Group check happens at request-time (no DB hit at import-time)
        return user.groups.filter(name__in=["moderator", "Moderators"]).exists()

class IsElectionCreator(BasePermission):
    """Write access only for the object's .creator; reads are open."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "creator", None) == request.user

class IsVoter(BasePermission):
    """Write access only for the object's .voter; reads are open."""
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return getattr(obj, "voter", None) == request.user
