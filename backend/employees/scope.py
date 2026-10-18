
from access_control.models import UserAssignment
from organization.models import Plant


HR_ROLE_CODES = {
    "CENTRAL_HR",
    "PLANT_HR_MANAGER",
    "PLANT_HR_EXECUTIVE",
}


def get_hr_assignments(user, legal_entity_id, required_permission):
    return UserAssignment.objects.filter(
        user=user,
        legal_entity_id=legal_entity_id,
        is_active=True,
        role__is_active=True,
        role__functional_area__code="CORPORATE_GOVERNANCE",
        role__code__in=HR_ROLE_CODES,
        role__role_permissions__permission__code=required_permission,
        role__role_permissions__permission__is_active=True,
    ).select_related(
        "role",
        "plant",
        "legal_entity",
    )


def get_authorized_plant_ids(user, legal_entity_id, required_permission):
    assignments = get_hr_assignments(
        user,
        legal_entity_id,
        required_permission,
    )

    has_entity_wide_access = assignments.filter(
        role__code="CENTRAL_HR",
        plant__isnull=True,
    ).exists()

    plant_ids = set(
        assignments.exclude(
            plant__isnull=True,
        ).filter(
            plant__legal_entity_id=legal_entity_id,
            plant__is_active=True,
        ).values_list(
            "plant_id",
            flat=True,
        ).distinct()
    )

    return has_entity_wide_access, plant_ids


def can_access_plant(user, legal_entity_id, plant_id, required_permission):
    if not plant_id:
        return False

    plant_exists = Plant.objects.filter(
        pk=plant_id,
        legal_entity_id=legal_entity_id,
        is_active=True,
    ).exists()

    if not plant_exists:
        return False

    all_plants, plant_ids = get_authorized_plant_ids(
        user,
        legal_entity_id,
        required_permission,
    )

    if all_plants:
        return True

    return plant_id in plant_ids
