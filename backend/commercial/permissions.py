
from rest_framework.permissions import BasePermission

from access_control.models import UserAssignment


class HasCommercialPermission(BasePermission):
    """
    Require an active role assignment with the requested commercial
    permission for the selected legal entity.
    """

    message = "You do not have permission to access this commercial resource."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated or not user.is_active:
            return False

        required_permission = getattr(
            view,
            "required_permission",
            None,
        )

        if not required_permission:
            return False

        legal_entity_id = request.query_params.get("legal_entity_id")

        # For creation requests, the API will validate the legal entity
        # from the submitted payload separately.
        if not legal_entity_id:
            legal_entity_id = request.data.get("legal_entity_id")

        if not legal_entity_id:
            return False

        return UserAssignment.objects.filter(
            user=user,
            legal_entity_id=legal_entity_id,
            is_active=True,
            role__is_active=True,
            role__role_permissions__permission__code=required_permission,
            role__role_permissions__permission__is_active=True,
        ).exists()
