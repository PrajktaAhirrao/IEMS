
from django.core.exceptions import ValidationError
from django.db import models


class Enterprise(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class BusinessGroup(models.Model):
    enterprise = models.ForeignKey(
        Enterprise,
        on_delete=models.PROTECT,
        related_name="business_groups",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["enterprise", "code"],
                name="uq_business_group_code_per_enterprise",
            ),
        ]

    def __str__(self):
        return self.name


class LegalEntity(models.Model):
    business_group = models.ForeignKey(
        BusinessGroup,
        on_delete=models.PROTECT,
        related_name="legal_entities",
    )
    code = models.CharField(max_length=50)
    legal_name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["legal_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["business_group", "code"],
                name="uq_legal_entity_code_per_group",
            ),
        ]

    def __str__(self):
        return self.display_name


class Plant(models.Model):
    legal_entity = models.ForeignKey(
        LegalEntity,
        on_delete=models.PROTECT,
        related_name="plants",
    )
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["legal_entity", "code"],
                name="uq_plant_code_per_legal_entity",
            ),
        ]

    def __str__(self):
        return self.name


class OrganizationalGroup(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class FunctionalArea(models.Model):
    group = models.ForeignKey(
        OrganizationalGroup,
        on_delete=models.PROTECT,
        related_name="functional_areas",
        null=True,
        blank=True,
    )

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DepartmentDefinition(models.Model):
    class ScopeType(models.TextChoices):
        CENTRAL = "CENTRAL", "Central"
        PLANT = "PLANT", "Plant-scoped"

    functional_area = models.ForeignKey(
        FunctionalArea,
        on_delete=models.PROTECT,
        related_name="departments",
    )

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)

    scope_type = models.CharField(
        max_length=20,
        choices=ScopeType.choices,
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["functional_area__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["functional_area", "name"],
                name="uq_department_name_per_functional_area",
            ),
        ]

    def __str__(self):
        return self.name


class OrganizationalUnit(models.Model):
    class ScopeType(models.TextChoices):
        CENTRAL = "CENTRAL", "Central"
        PLANT = "PLANT", "Plant-scoped"

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)

    legal_entity = models.ForeignKey(
        LegalEntity,
        on_delete=models.PROTECT,
        related_name="organizational_units",
    )

    department = models.ForeignKey(
        DepartmentDefinition,
        on_delete=models.PROTECT,
        related_name="organizational_units",
    )

    scope_type = models.CharField(
        max_length=20,
        choices=ScopeType.choices,
    )

    plant = models.ForeignKey(
        Plant,
        on_delete=models.PROTECT,
        related_name="owned_organizational_units",
        null=True,
        blank=True,
    )

    served_plants = models.ManyToManyField(
        Plant,
        related_name="served_by_organizational_units",
        blank=True,
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        scope_type="CENTRAL",
                        plant__isnull=True,
                    )
                    | models.Q(
                        scope_type="PLANT",
                        plant__isnull=False,
                    )
                ),
                name="ck_ou_scope_requires_correct_plant",
            ),
            models.UniqueConstraint(
                fields=["legal_entity", "department"],
                condition=models.Q(scope_type="CENTRAL"),
                name="uq_central_ou_per_department_legal_entity",
            ),
            models.UniqueConstraint(
                fields=["legal_entity", "department", "plant"],
                condition=models.Q(scope_type="PLANT"),
                name="uq_plant_ou_per_department_plant",
            ),
        ]

    def clean(self):
        errors = {}

        if self.department_id:
            if self.scope_type != self.department.scope_type:
                errors["scope_type"] = (
                    "Organizational Unit scope must match "
                    "the Department Definition scope."
                )

        if self.scope_type == self.ScopeType.CENTRAL:
            if self.plant_id is not None:
                errors["plant"] = (
                    "Central Organizational Units cannot be owned by a plant."
                )

        if self.scope_type == self.ScopeType.PLANT:
            if self.plant_id is None:
                errors["plant"] = (
                    "Plant-scoped Organizational Units must belong to a plant."
                )

        if self.plant_id and self.legal_entity_id:
            if self.plant.legal_entity_id != self.legal_entity_id:
                errors["plant"] = (
                    "The selected plant must belong to the same Legal Entity."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name
