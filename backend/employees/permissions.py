
from rest_framework.permissions import BasePermission

from .scope import can_access_plant, get_hr_assignments


class HasEmployeeMasterPermission(BasePermission):
    message = (
        "You do not have Employee Master access to this legal entity "
        "or plant."
    )

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated or not user.is_active:
            return False

        required_permission = getattr(view, "required_permission", None)
        if not required_permission:
            return False

        legal_entity_id = request.query_params.get("legal_entity_id")
        if not legal_entity_id:
            legal_entity_id = request.data.get("legal_entity_id")
        if not legal_entity_id:
            legal_entity_id = request.data.get("legal_entity")

        if not legal_entity_id or not str(legal_entity_id).isdigit():
            return False

        assignments = get_hr_assignments(
            user,
            legal_entity_id,
            required_permission,
        )

        if not assignments.exists():
            return False

        plant_id = request.query_params.get("plant_id")
        if not plant_id:
            plant_id = request.data.get("plant_id")
        if not plant_id:
            plant_id = request.data.get("plant")

        # Central HR may list all plants in its assigned legal entity.

        # The list view applies the entity and plant scope to the queryset.
        # Central HR can list entity-wide; plant HR can list its assigned plants.
        if request.method == "GET" and not plant_id:
            return True


        if not plant_id or not str(plant_id).isdigit():
            return False

        return can_access_plant(
            user,
            legal_entity_id,
            int(plant_id),
            required_permission,
        )
