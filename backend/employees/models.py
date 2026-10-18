
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Employee(models.Model):
    class EmploymentType(models.TextChoices):
        PERMANENT = "PERMANENT", "Permanent"
        CONTRACT = "CONTRACT", "Contract"
        TRAINEE = "TRAINEE", "Trainee"
        CONSULTANT = "CONSULTANT", "Consultant"

    class EmploymentStatus(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ON_LEAVE = "ON_LEAVE", "On Leave"
        SUSPENDED = "SUSPENDED", "Suspended"
        SEPARATED = "SEPARATED", "Separated"

    class RecordStatus(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING_VERIFICATION = (
            "PENDING_VERIFICATION",
            "Pending Verification",
        )
        VERIFIED = "VERIFIED", "Verified"


    

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    employee_code = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        editable=False,
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_profile",
    )

    # 01 — Employee Identity
    full_name = models.CharField(max_length=200, blank=True)
    preferred_name = models.CharField(max_length=100, blank=True)
    profile_photo = models.ImageField(
        upload_to="employees/profile_photos/",
        null=True,
        blank=True,
    )
    date_of_birth = models.DateField(null=True, blank=True)
    date_of_joining = models.DateField(null=True, blank=True)

    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        blank=True,
    )
    employment_status = models.CharField(
        max_length=20,
        choices=EmploymentStatus.choices,
        default=EmploymentStatus.ACTIVE,
    )
    record_status = models.CharField(
        max_length=30,
        choices=RecordStatus.choices,
        default=RecordStatus.DRAFT,
    )

    # 02 — Organizational Information
    legal_entity = models.ForeignKey(
        "organization.LegalEntity",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employees",
    )
    plant = models.ForeignKey(
        "organization.Plant",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employees",
    )
    department = models.ForeignKey(
        "organization.DepartmentDefinition",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employees",
    )
    organizational_unit = models.ForeignKey(
        "organization.OrganizationalUnit",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employees",
    )
    designation = models.CharField(max_length=150, blank=True)
    reporting_manager = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="direct_reports",
    )
    work_location = models.CharField(max_length=200, blank=True)

    # 03 — Personal Details and Contact Information
    personal_email = models.EmailField(blank=True)
    personal_mobile = models.CharField(max_length=20, blank=True)
    whatsapp_available = models.BooleanField(null=True, blank=True)
    current_address = models.TextField(blank=True)
    permanent_address = models.TextField(blank=True)

    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_relationship = models.CharField(
        max_length=50,
        blank=True,
    )
    emergency_contact_mobile = models.CharField(max_length=20, blank=True)

    # Record ownership and audit timestamps
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="employee_records_created",
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employee_records_verified",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee_code"]
        verbose_name = "Employee"
        verbose_name_plural = "Employees"


    

    def save(self, *args, **kwargs):
        """Generate a system-controlled employee code for new records."""
        if not self.employee_code:
            self.employee_code = f"EMP-{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        errors = {}

        if self.plant_id:
            if (
                self.legal_entity_id
                and self.plant.legal_entity_id != self.legal_entity_id
            ):
                errors["plant"] = (
                    "The selected plant must belong to the selected "
                    "legal entity."
                )
            elif not self.legal_entity_id:
                errors["legal_entity"] = (
                    "Select a legal entity before assigning a plant."
                )

            if not self.plant.is_active:
                errors["plant"] = "Employees cannot be assigned to an inactive plant."

        if self.legal_entity_id and not self.legal_entity.is_active:
            errors["legal_entity"] = (
                "Employees cannot be assigned to an inactive legal entity."
            )

        if self.department_id and self.department.functional_area_id:
            if (
                self.organizational_unit_id
                and self.organizational_unit.department_id != self.department_id
            ):
                errors["organizational_unit"] = (
                    "The organizational unit must match the selected department."
                )

        if self.organizational_unit_id:
            unit = self.organizational_unit

            if (
                self.legal_entity_id
                and unit.legal_entity_id != self.legal_entity_id
            ):
                errors["organizational_unit"] = (
                    "The organizational unit must belong to the selected "
                    "legal entity."
                )

            if (
                self.department_id
                and unit.department_id != self.department_id
            ):
                errors["organizational_unit"] = (
                    "The organizational unit must match the selected department."
                )

            if (
                self.plant_id
                and unit.scope_type == "PLANT"
                and unit.plant_id != self.plant_id
                and not unit.served_plants.filter(
                    pk=self.plant_id
                ).exists()
            ):
                errors["organizational_unit"] = (
                    "The organizational unit is not assigned to the selected plant."
                )

        if self.reporting_manager_id == self.pk and self.pk:
            errors["reporting_manager"] = (
                "An employee cannot report to themselves."
            )

        if self.record_status == self.RecordStatus.VERIFIED:
            required_fields = {
                "full_name": self.full_name,
                "date_of_joining": self.date_of_joining,
                "employment_type": self.employment_type,
                "legal_entity": self.legal_entity_id,
                "department": self.department_id,
                "designation": self.designation,
            }
            missing = [
                field
                for field, value in required_fields.items()
                if not value
            ]

            if missing:
                errors["record_status"] = (
                    "A record cannot be verified while required fields "
                    "are incomplete: " + ", ".join(missing)
                )

            if not self.verified_by_id:
                errors["verified_by"] = (
                    "A verified employee record must identify the verifying user."
                )

            if not self.verified_at:
                errors["verified_at"] = (
                    "A verified employee record must have a verification timestamp."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.employee_code} - {self.full_name or 'Name Pending'}"


class EmployeeDocument(models.Model):
    class VerificationStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        VERIFIED = "VERIFIED", "Verified"
        REJECTED = "REJECTED", "Rejected"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    document_type = models.CharField(max_length=80)
    holder_name = models.CharField(max_length=200, blank=True)
    document_number = models.CharField(max_length=150, blank=True)
    file = models.FileField(upload_to="employees/restricted_documents/")
    issued_by = models.CharField(max_length=200, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employee_documents_verified",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="employee_documents_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document_type", "-created_at"]

    def clean(self):
        super().clean()
        if self.verification_status == self.VerificationStatus.VERIFIED:
            errors = {}
            if not self.verified_by_id:
                errors["verified_by"] = (
                    "A verified document must identify the verifying user."
                )
            if not self.verified_at:
                errors["verified_at"] = (
                    "A verified document must have a verification timestamp."
                )
            if errors:
                raise ValidationError(errors)

    def __str__(self):
        return f"{self.employee.employee_code} — {self.document_type}"


class EmployeeEducation(models.Model):
    class EducationLevel(models.TextChoices):
        SSC = "SSC", "SSC / 10th"
        HSC = "HSC", "HSC / 12th"
        ITI = "ITI", "ITI / Trade Certificate"
        APPRENTICESHIP = "APPRENTICESHIP", "Apprenticeship"
        DIPLOMA = "DIPLOMA", "Diploma / Polytechnic"
        UNDERGRADUATE = "UNDERGRADUATE", "Undergraduate"
        POSTGRADUATE = "POSTGRADUATE", "Postgraduate"
        DOCTORATE = "DOCTORATE", "Doctorate"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="education_records",
    )
    education_level = models.CharField(
        max_length=30,
        choices=EducationLevel.choices,
    )
    qualification = models.CharField(max_length=200)
    institution = models.CharField(max_length=200, blank=True)
    board_or_university = models.CharField(max_length=200, blank=True)
    passing_year = models.PositiveSmallIntegerField(null=True, blank=True)
    result_or_grade = models.CharField(max_length=100, blank=True)
    proof_document = models.FileField(
        upload_to="employees/education_proofs/",
        null=True,
        blank=True,
    )
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employee_education_verified",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-passing_year", "education_level"]

    def __str__(self):
        return f"{self.employee.employee_code} — {self.qualification}"


class EmployeeProfessionalQualification(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="professional_qualifications",
    )
    qualification_name = models.CharField(max_length=200)
    issuing_organization = models.CharField(max_length=200, blank=True)
    certificate_reference = models.CharField(max_length=150, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    proof_document = models.FileField(
        upload_to="employees/qualification_proofs/",
        null=True,
        blank=True,
    )
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employee_qualifications_verified",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["qualification_name"]

    def __str__(self):
        return f"{self.employee.employee_code} — {self.qualification_name}"


class EmployeeSkill(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="skills",
    )
    skill_name = models.CharField(max_length=200)
    skill_category = models.CharField(max_length=100, blank=True)
    proficiency_level = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employee_skills_verified",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["skill_name"]

    def __str__(self):
        return f"{self.employee.employee_code} — {self.skill_name}"


class EmployeeTraining(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="training_records",
    )
    training_name = models.CharField(max_length=200)
    provider = models.CharField(max_length=200, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    certificate_reference = models.CharField(max_length=150, blank=True)
    valid_until = models.DateField(null=True, blank=True)
    certificate_file = models.FileField(
        upload_to="employees/training_certificates/",
        null=True,
        blank=True,
    )
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="employee_training_verified",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completion_date", "training_name"]

    def __str__(self):
        return f"{self.employee.employee_code} — {self.training_name}"

