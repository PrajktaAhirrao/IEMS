from django.db import migrations


def seed_initial_structure(apps, schema_editor):
    Enterprise = apps.get_model("organization", "Enterprise")
    BusinessGroup = apps.get_model("organization", "BusinessGroup")
    LegalEntity = apps.get_model("organization", "LegalEntity")
    Plant = apps.get_model("organization", "Plant")
    FunctionalArea = apps.get_model("organization", "FunctionalArea")
    DepartmentDefinition = apps.get_model(
        "organization",
        "DepartmentDefinition",
    )
    OrganizationalUnit = apps.get_model(
        "organization",
        "OrganizationalUnit",
    )

    enterprise, _ = Enterprise.objects.get_or_create(
        code="IEMS",
        defaults={
            "name": "IEMS",
            "is_active": True,
        },
    )

    business_group, _ = BusinessGroup.objects.get_or_create(
        enterprise=enterprise,
        code="IEMS-GRP",
        defaults={
            "name": "IEMS Business / Controlling Group",
            "is_active": True,
        },
    )

    legal_entity, _ = LegalEntity.objects.get_or_create(
        business_group=business_group,
        code="IEMS-MFG",
        defaults={
            "legal_name": "IEMS Manufacturing Industries Pvt. Ltd.",
            "display_name": "IEMS Manufacturing Industries Pvt. Ltd.",
            "is_active": True,
        },
    )

    plant_1, _ = Plant.objects.get_or_create(
        legal_entity=legal_entity,
        code="PLANT-01",
        defaults={
            "name": "Plant 1 — Integrated Manufacturing Plant",
            "is_active": True,
        },
    )

    plant_2, _ = Plant.objects.get_or_create(
        legal_entity=legal_entity,
        code="PLANT-02",
        defaults={
            "name": "Plant 2 — Specialized Steel Wire Processing Plant",
            "is_active": True,
        },
    )

    commercial, _ = FunctionalArea.objects.get_or_create(
        code="COMMERCIAL",
        defaults={
            "name": "Commercial",
            "is_active": True,
        },
    )

    sales_department, _ = DepartmentDefinition.objects.get_or_create(
        code="COM-SCM",
        defaults={
            "functional_area": commercial,
            "name": "Sales & Customer Management",
            "scope_type": "CENTRAL",
            "is_active": True,
        },
    )

    marketing_department, _ = DepartmentDefinition.objects.get_or_create(
        code="COM-MBD",
        defaults={
            "functional_area": commercial,
            "name": "Marketing / Business Development",
            "scope_type": "CENTRAL",
            "is_active": True,
        },
    )

    contracts_department, _ = DepartmentDefinition.objects.get_or_create(
        code="COM-CCM",
        defaults={
            "functional_area": commercial,
            "name": "Contracts & Commercial Management",
            "scope_type": "CENTRAL",
            "is_active": True,
        },
    )

    sales_ou, _ = OrganizationalUnit.objects.get_or_create(
        code="OU-COM-SCM",
        defaults={
            "name": "Central Sales & Customer Management",
            "legal_entity": legal_entity,
            "department": sales_department,
            "scope_type": "CENTRAL",
            "plant": None,
            "is_active": True,
        },
    )

    marketing_ou, _ = OrganizationalUnit.objects.get_or_create(
        code="OU-COM-MBD",
        defaults={
            "name": "Central Marketing / Business Development",
            "legal_entity": legal_entity,
            "department": marketing_department,
            "scope_type": "CENTRAL",
            "plant": None,
            "is_active": True,
        },
    )

    contracts_ou, _ = OrganizationalUnit.objects.get_or_create(
        code="OU-COM-CCM",
        defaults={
            "name": "Central Contracts & Commercial Management",
            "legal_entity": legal_entity,
            "department": contracts_department,
            "scope_type": "CENTRAL",
            "plant": None,
            "is_active": True,
        },
    )

    for ou in [sales_ou, marketing_ou, contracts_ou]:
        ou.served_plants.add(plant_1, plant_2)


def unseed_initial_structure(apps, schema_editor):
    OrganizationalUnit = apps.get_model(
        "organization",
        "OrganizationalUnit",
    )
    DepartmentDefinition = apps.get_model(
        "organization",
        "DepartmentDefinition",
    )
    FunctionalArea = apps.get_model(
        "organization",
        "FunctionalArea",
    )
    Plant = apps.get_model("organization", "Plant")
    LegalEntity = apps.get_model("organization", "LegalEntity")
    BusinessGroup = apps.get_model("organization", "BusinessGroup")
    Enterprise = apps.get_model("organization", "Enterprise")

    OrganizationalUnit.objects.filter(
        code__in=[
            "OU-COM-SCM",
            "OU-COM-MBD",
            "OU-COM-CCM",
        ]
    ).delete()

    DepartmentDefinition.objects.filter(
        code__in=[
            "COM-SCM",
            "COM-MBD",
            "COM-CCM",
        ]
    ).delete()

    FunctionalArea.objects.filter(
        code="COMMERCIAL"
    ).delete()

    Plant.objects.filter(
        code__in=[
            "PLANT-01",
            "PLANT-02",
        ]
    ).delete()

    LegalEntity.objects.filter(
        code="IEMS-MFG"
    ).delete()

    BusinessGroup.objects.filter(
        code="IEMS-GRP"
    ).delete()

    Enterprise.objects.filter(
        code="IEMS"
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("organization", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            seed_initial_structure,
            unseed_initial_structure,
        ),
    ]