from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from organization.models import (
    DepartmentDefinition,
    FunctionalArea,
    LegalEntity,
    OrganizationalUnit,
)


class Role(models.Model):
    class ScopeLevel(models.TextChoices):
        FUNCTIONAL_AREA = "FUNCTIONAL_AREA", "Functional Area"
        ORGANIZATIONAL_UNIT = "ORGANIZATIONAL_UNIT", "Organizational Unit"

    code = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=150)

    functional_area = models.ForeignKey(
        FunctionalArea,
        on_delete=models.PROTECT,
        related_name="roles",
    )

    department = models.ForeignKey(
        DepartmentDefinition,
        on_delete=models.PROTECT,
        related_name="roles",
        null=True,
        blank=True,
    )

    scope_level = models.CharField(
        max_length=30,
        choices=ScopeLevel.choices,
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["functional_area__name", "name"]
        constraints = [
            models.UniqueConstraint(
                fields=["functional_area", "name"],
                name="uq_role_name_per_functional_area",
            ),
        ]

    def clean(self):
        errors = {}

        if self.scope_level == self.ScopeLevel.FUNCTIONAL_AREA:
            if self.department_id is not None:
                errors["department"] = (
                    "Functional-area roles cannot be tied to a single department."
                )

        if self.scope_level == self.ScopeLevel.ORGANIZATIONAL_UNIT:
            if self.department_id is None:
                errors["department"] = (
                    "Organizational-unit roles must reference a department."
                )

        if self.department_id and self.functional_area_id:
            if self.department.functional_area_id != self.functional_area_id:
                errors["department"] = (
                    "Role department must belong to the selected functional area."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Permission(models.Model):
    code = models.CharField(max_length=120, unique=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return self.code


class RolePermission(models.Model):
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )

    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name="role_permissions",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["role", "permission"],
                name="uq_role_permission",
            ),
        ]

    def __str__(self):
        return f"{self.role} → {self.permission}"




class UserAssignment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="assignments",
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="user_assignments",
    )

    legal_entity = models.ForeignKey(
        LegalEntity,
        on_delete=models.PROTECT,
        related_name="user_assignments",
    )

    plant = models.ForeignKey(
        "organization.Plant",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="user_assignments",
    )

    organizational_unit = models.ForeignKey(
        OrganizationalUnit,
        on_delete=models.PROTECT,
        related_name="user_assignments",
        null=True,
        blank=True,
    )

    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["user_id", "role__name"]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "role",
                    "legal_entity",
                    "organizational_unit",
                    "plant",
                ],
                name="uq_user_role_org_plant_assignment",
            ),
        ]

    def clean(self):
        errors = {}

        # Prevent assignments to inactive users, roles, or organizations.
        if self.user_id and not self.user.is_active:
            errors["user"] = "Inactive users cannot receive assignments."

        if self.role_id and not self.role.is_active:
            errors["role"] = "Inactive roles cannot be assigned."

        if self.legal_entity_id and not self.legal_entity.is_active:
            errors["legal_entity"] = (
                "Assignments cannot be created for inactive legal entities."
            )

        if self.plant_id and not self.plant.is_active:
            errors["plant"] = (
                "Assignments cannot be created for inactive plants."
            )

        # Validate role scope.
        if self.role_id:
            if self.role.scope_level == Role.ScopeLevel.FUNCTIONAL_AREA:
                if self.organizational_unit_id is not None:
                    errors["organizational_unit"] = (
                        "Functional-area roles must not be restricted "
                        "to one Organizational Unit."
                    )

            elif self.role.scope_level == Role.ScopeLevel.ORGANIZATIONAL_UNIT:
                if self.organizational_unit_id is None:
                    errors["organizational_unit"] = (
                        "Organizational-unit roles require an Organizational Unit."
                    )

        # Validate organizational-unit ownership.
        if self.organizational_unit_id and self.legal_entity_id:
            if self.organizational_unit.legal_entity_id != self.legal_entity_id:
                errors["organizational_unit"] = (
                    "Organizational Unit must belong to the selected Legal Entity."
                )

        # Validate department scope.
        if (
            self.role_id
            and self.organizational_unit_id
            and self.role.department_id
            and self.organizational_unit.department_id != self.role.department_id
        ):
            errors["organizational_unit"] = (
                "Organizational Unit must match the department "
                "defined for this role."
            )

        # Validate plant ownership, even without an organizational unit.
        if self.plant_id and self.legal_entity_id:
            if self.plant.legal_entity_id != self.legal_entity_id:
                errors["plant"] = (
                    "Plant must belong to the selected Legal Entity."
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user} — {self.role}"
