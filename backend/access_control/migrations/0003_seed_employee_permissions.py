from django.db import migrations


def create_employee_permissions(apps, schema_editor):
    Permission = apps.get_model("access_control", "Permission")

    permissions = [
        {
            "code": "employees.employee_master.view",
            "name": "View Employee Master",
            "description": (
                "View employee records within authorized legal entities."
            ),
        },
        {
            "code": "employees.employee_master.manage",
            "name": "Manage Employee Master",
            "description": (
                "Create and update official employee records within "
                "authorized legal entities."
            ),
        },
    ]

    for item in permissions:
        Permission.objects.update_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "description": item["description"],
                "is_active": True,
            },
        )


def remove_employee_permissions(apps, schema_editor):
    Permission = apps.get_model("access_control", "Permission")

    Permission.objects.filter(
        code__in=[
            "employees.employee_master.view",
            "employees.employee_master.manage",
        ]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("access_control", "0002_seed_commercial_roles"),
    ]

    operations = [
        migrations.RunPython(
            create_employee_permissions,
            remove_employee_permissions,
        ),
    ]