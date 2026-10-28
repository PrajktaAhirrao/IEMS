
from django.db import migrations


def seed_corporate_governance_functional_area(apps, schema_editor):
    FunctionalArea = apps.get_model("organization", "FunctionalArea")

    FunctionalArea.objects.get_or_create(
        code="CORPORATE_GOVERNANCE",
        defaults={
            "name": "Corporate & Governance",
            "is_active": True,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("organization", "0004_organizationalgroup_functionalarea_group"),
    ]

    operations = [
        migrations.RunPython(
            seed_corporate_governance_functional_area,
            migrations.RunPython.noop,
        ),
    ]
