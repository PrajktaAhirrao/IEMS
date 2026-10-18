
from django.db import migrations


HR_PERMISSIONS = [
    (
        "employees.hr_operations.approve",
        "Approve HR Operations",
        "Approve authorized plant-level HR operations.",
    ),
    (
        "access_control.hr_assignments.manage",
        "Manage HR Role Assignments",
        "Appoint, change, or revoke privileged HR role assignments.",
    ),
]


HR_ROLES = [
    {
        "code": "CENTRAL_HR",
        "name": "Central HR",
        "permissions": [
            "employees.employee_master.view",
            "employees.employee_master.manage",
            "employees.hr_operations.approve",
        ],
    },
    {
        "code": "PLANT_HR_MANAGER",
        "name": "Plant HR Manager",
        "permissions": [
            "employees.employee_master.view",
            "employees.employee_master.manage",
            "employees.hr_operations.approve",
        ],
    },
    {
        "code": "PLANT_HR_EXECUTIVE",
        "name": "Plant HR Executive",
        "permissions": [
            "employees.employee_master.view",
            "employees.employee_master.manage",
        ],
    },
]


def seed_hr_roles_and_permissions(apps, schema_editor):
    FunctionalArea = apps.get_model("organization", "FunctionalArea")
    Role = apps.get_model("access_control", "Role")
    Permission = apps.get_model("access_control", "Permission")
    RolePermission = apps.get_model("access_control", "RolePermission")

    hr_area = FunctionalArea.objects.get(code="HR")

    for code, name, description in HR_PERMISSIONS:
        Permission.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "description": description,
                "is_active": True,
            },
        )

    for role_data in HR_ROLES:
        role, _ = Role.objects.update_or_create(
            code=role_data["code"],
            defaults={
                "name": role_data["name"],
                "functional_area": hr_area,
                "department": None,
                "scope_level": "FUNCTIONAL_AREA",
                "is_active": True,
            },
        )

        for permission_code in role_data["permissions"]:
            permission = Permission.objects.get(code=permission_code)
            RolePermission.objects.get_or_create(
                role=role,
                permission=permission,
            )

    # Create a separate management permission, but do not grant it
    # to any operational HR role.
    management_permission = Permission.objects.get(
        code="access_control.hr_assignments.manage"
    )

    # Deliberately do not attach this permission to any role here.
    # A separate, explicitly authorized management role will control it.


def reverse_seed_hr_roles_and_permissions(apps, schema_editor):
    Role = apps.get_model("access_control", "Role")
    Permission = apps.get_model("access_control", "Permission")
    RolePermission = apps.get_model("access_control", "RolePermission")

    role_codes = [
        "CENTRAL_HR",
        "PLANT_HR_MANAGER",
        "PLANT_HR_EXECUTIVE",
    ]

    seeded_roles = Role.objects.filter(code__in=role_codes)
    RolePermission.objects.filter(role__in=seeded_roles).delete()
    seeded_roles.delete()

    Permission.objects.filter(
        code__in=[
            "employees.hr_operations.approve",
            "access_control.hr_assignments.manage",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("organization", "0003_seed_hr_functional_area"),
        ("access_control", "0005_userassignment_plant"),
    ]

    operations = [
        migrations.RunPython(
            seed_hr_roles_and_permissions,
            reverse_seed_hr_roles_and_permissions,
        ),
    ]
