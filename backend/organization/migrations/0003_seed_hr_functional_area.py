from django.db import migrations


def create_hr_functional_area(apps, schema_editor):
    FunctionalArea = apps.get_model(
        "organization",
        "FunctionalArea",
    )

    FunctionalArea.objects.update_or_create(
        code="HR",
        defaults={
            "name": "Human Resources",
            "is_active": True,
        },
    )


def remove_hr_functional_area(apps, schema_editor):
    FunctionalArea = apps.get_model(
        "organization",
        "FunctionalArea",
    )

    # Delete only if no roles reference this functional area.
    hr_area = FunctionalArea.objects.filter(code="HR").first()

    if hr_area and not hr_area.roles.exists():
        hr_area.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("organization", "0002_seed_initial_structure"),
    ]

    operations = [
        migrations.RunPython(
            create_hr_functional_area,
            remove_hr_functional_area,
        ),
    ]