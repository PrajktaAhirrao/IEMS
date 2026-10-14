from django.db import migrations


def seed_commercial_roles(apps, schema_editor):
    FunctionalArea = apps.get_model(
        "organization",
        "FunctionalArea",
    )
    DepartmentDefinition = apps.get_model(
        "organization",
        "DepartmentDefinition",
    )

    Role = apps.get_model(
        "access_control",
        "Role",
    )
    Permission = apps.get_model(
        "access_control",
        "Permission",
    )
    RolePermission = apps.get_model(
        "access_control",
        "RolePermission",
    )

    commercial = FunctionalArea.objects.get(
        code="COMMERCIAL"
    )

    sales_department = DepartmentDefinition.objects.get(
        code="COM-SCM"
    )

    marketing_department = DepartmentDefinition.objects.get(
        code="COM-MBD"
    )

    contracts_department = DepartmentDefinition.objects.get(
        code="COM-CCM"
    )

    # Roles

    front_desk_role, _ = Role.objects.get_or_create(
        code="COMMERCIAL_FRONT_DESK_EXECUTIVE",
        defaults={
            "name": "Commercial Front Desk Executive",
            "functional_area": commercial,
            "department": None,
            "scope_level": "FUNCTIONAL_AREA",
            "is_active": True,
        },
    )

    bd_manager_role, _ = Role.objects.get_or_create(
        code="BD_MANAGER",
        defaults={
            "name": "BD Manager",
            "functional_area": commercial,
            "department": marketing_department,
            "scope_level": "ORGANIZATIONAL_UNIT",
            "is_active": True,
        },
    )

    bd_executive_role, _ = Role.objects.get_or_create(
        code="BD_EXECUTIVE",
        defaults={
            "name": "BD Executive",
            "functional_area": commercial,
            "department": marketing_department,
            "scope_level": "ORGANIZATIONAL_UNIT",
            "is_active": True,
        },
    )

    sales_manager_role, _ = Role.objects.get_or_create(
        code="SALES_MANAGER",
        defaults={
            "name": "Sales Manager",
            "functional_area": commercial,
            "department": sales_department,
            "scope_level": "ORGANIZATIONAL_UNIT",
            "is_active": True,
        },
    )

    sales_executive_role, _ = Role.objects.get_or_create(
        code="SALES_EXECUTIVE",
        defaults={
            "name": "Sales Executive",
            "functional_area": commercial,
            "department": sales_department,
            "scope_level": "ORGANIZATIONAL_UNIT",
            "is_active": True,
        },
    )

    contracts_manager_role, _ = Role.objects.get_or_create(
        code="CONTRACTS_COMMERCIAL_MANAGER",
        defaults={
            "name": "Contracts / Commercial Manager",
            "functional_area": commercial,
            "department": contracts_department,
            "scope_level": "ORGANIZATIONAL_UNIT",
            "is_active": True,
        },
    )

    contracts_executive_role, _ = Role.objects.get_or_create(
        code="CONTRACTS_COMMERCIAL_EXECUTIVE",
        defaults={
            "name": "Contracts / Commercial Executive",
            "functional_area": commercial,
            "department": contracts_department,
            "scope_level": "ORGANIZATIONAL_UNIT",
            "is_active": True,
        },
    )

    # Workspace permissions

    front_desk_access, _ = Permission.objects.get_or_create(
        code="commercial.front_desk.access",
        defaults={
            "name": "Access Commercial Front Desk",
            "description": (
                "Allows access to the Commercial Front Desk workspace."
            ),
            "is_active": True,
        },
    )

    marketing_access, _ = Permission.objects.get_or_create(
        code="commercial.marketing.access",
        defaults={
            "name": "Access Marketing / Business Development",
            "description": (
                "Allows access to the Marketing / "
                "Business Development workspace."
            ),
            "is_active": True,
        },
    )

    sales_access, _ = Permission.objects.get_or_create(
        code="commercial.sales.access",
        defaults={
            "name": "Access Sales & Customer Management",
            "description": (
                "Allows access to the Sales & "
                "Customer Management workspace."
            ),
            "is_active": True,
        },
    )

    contracts_access, _ = Permission.objects.get_or_create(
        code="commercial.contracts.access",
        defaults={
            "name": "Access Contracts & Commercial Management",
            "description": (
                "Allows access to the Contracts & "
                "Commercial Management workspace."
            ),
            "is_active": True,
        },
    )

    mappings = [
        (front_desk_role, front_desk_access),
        (bd_manager_role, marketing_access),
        (bd_executive_role, marketing_access),
        (sales_manager_role, sales_access),
        (sales_executive_role, sales_access),
        (contracts_manager_role, contracts_access),
        (contracts_executive_role, contracts_access),
    ]

    for role, permission in mappings:
        RolePermission.objects.get_or_create(
            role=role,
            permission=permission,
        )


def unseed_commercial_roles(apps, schema_editor):
    RolePermission = apps.get_model(
        "access_control",
        "RolePermission",
    )
    Role = apps.get_model(
        "access_control",
        "Role",
    )
    Permission = apps.get_model(
        "access_control",
        "Permission",
    )

    role_codes = [
        "COMMERCIAL_FRONT_DESK_EXECUTIVE",
        "BD_MANAGER",
        "BD_EXECUTIVE",
        "SALES_MANAGER",
        "SALES_EXECUTIVE",
        "CONTRACTS_COMMERCIAL_MANAGER",
        "CONTRACTS_COMMERCIAL_EXECUTIVE",
    ]

    permission_codes = [
        "commercial.front_desk.access",
        "commercial.marketing.access",
        "commercial.sales.access",
        "commercial.contracts.access",
    ]

    roles = Role.objects.filter(code__in=role_codes)
    permissions = Permission.objects.filter(
        code__in=permission_codes
    )

    RolePermission.objects.filter(
        role__in=roles,
        permission__in=permissions,
    ).delete()

    roles.delete()
    permissions.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("access_control", "0001_initial"),
        ("organization", "0002_seed_initial_structure"),
    ]

    operations = [
        migrations.RunPython(
            seed_commercial_roles,
            unseed_commercial_roles,
        ),
    ]

