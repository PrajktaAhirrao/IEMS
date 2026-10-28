
from django.db import migrations


HR_ROLE_CODES = [
    "HR_EMPLOYEE_MASTER_MANAGER",
    "CENTRAL_HR",
    "PLANT_HR_MANAGER",
    "PLANT_HR_EXECUTIVE",
]


def assign_hr_roles_to_corporate_governance(apps, schema_editor):
    FunctionalArea = apps.get_model("organization", "FunctionalArea")
    Role = apps.get_model("access_control", "Role")

    corporate_governance = FunctionalArea.objects.get(
        code="CORPORATE_GOVERNANCE"
    )

    Role.objects.filter(
        code__in=HR_ROLE_CODES,
    ).update(
        functional_area=corporate_governance,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("organization", "0005_seed_corporate_governance_functional_area"),
        ("access_control", "0008_useraccessevent"),
    ]

    operations = [
        migrations.RunPython(
            assign_hr_roles_to_corporate_governance,
            migrations.RunPython.noop,
        ),
    ]
