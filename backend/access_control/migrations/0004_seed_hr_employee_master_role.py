
from django.db import migrations


def seed_hr_employee_master_role(apps, schema_editor):
    FunctionalArea = apps.get_model("organization", "FunctionalArea")
    Role = apps.get_model("access_control", "Role")
    Permission = apps.get_model("access_control", "Permission")
    RolePermission = apps.get_model("access_control", "RolePermission")

    hr_area = FunctionalArea.objects.get(code="HR")

    hr_role, _ = Role.objects.update_or_create(
        code="HR_EMPLOYEE_MASTER_MANAGER",
        defaults={
            "name": "HR Employee Master Manager",
            "functional_area": hr_area,
            "department": None,
            "scope_level": "FUNCTIONAL_AREA",
            "is_active": True,
        },
    )

    permission_codes = [
        "employees.employee_master.view",
        "employees.employee_master.manage",
    ]

    for permission_code in permission_codes:
        permission = Permission.objects.get(code=permission_code)
        RolePermission.objects.get_or_create(
            role=hr_role,
            permission=permission,
        )


def reverse_seed_hr_employee_master_role(apps, schema_editor):
    Role = apps.get_model("access_control", "Role")
    RolePermission = apps.get_model("access_control", "RolePermission")

    hr_role = Role.objects.filter(
        code="HR_EMPLOYEE_MASTER_MANAGER"
    ).first()

    if hr_role:
        RolePermission.objects.filter(role=hr_role).delete()
        hr_role.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("organization", "0003_seed_hr_functional_area"),
        ("access_control", "0003_seed_employee_permissions"),
    ]

    operations = [
        migrations.RunPython(
            seed_hr_employee_master_role,
            reverse_seed_hr_employee_master_role,
        ),
    ]
