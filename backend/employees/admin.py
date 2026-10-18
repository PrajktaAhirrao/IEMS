
from django.contrib import admin

from .models import (
    Employee,
    EmployeeDocument,
    EmployeeEducation,
    EmployeeProfessionalQualification,
    EmployeeSkill,
    EmployeeTraining,
)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_code",
        "full_name",
        "legal_entity",
        "plant",
        "department",
        "employment_type",
        "employment_status",
        "record_status",
    )
    list_filter = (
        "legal_entity",
        "plant",
        "department",
        "employment_type",
        "employment_status",
        "record_status",
    )
    search_fields = (
        "employee_code",
        "full_name",
        "preferred_name",
        "personal_email",
        "personal_mobile",
    )
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "verified_at",
    )
    list_select_related = (
        "legal_entity",
        "plant",
        "department",
    )
    ordering = ("employee_code",)


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "document_type",
        "verification_status",
        "expiry_date",
        "verified_by",
        "verified_at",
    )
    list_filter = (
        "document_type",
        "verification_status",
        "expiry_date",
    )
    search_fields = (
        "employee__employee_code",
        "employee__full_name",
        "document_type",
        "holder_name",
    )
    readonly_fields = ("id", "created_at")


@admin.register(EmployeeEducation)
class EmployeeEducationAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "education_level",
        "qualification",
        "institution",
        "passing_year",
        "verified",
    )
    list_filter = ("education_level", "verified", "passing_year")
    search_fields = (
        "employee__employee_code",
        "employee__full_name",
        "qualification",
        "institution",
        "board_or_university",
    )
    readonly_fields = ("id", "created_at")


@admin.register(EmployeeProfessionalQualification)
class EmployeeProfessionalQualificationAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "qualification_name",
        "issuing_organization",
        "valid_until",
        "verified",
    )
    list_filter = ("verified", "valid_until")
    search_fields = (
        "employee__employee_code",
        "employee__full_name",
        "qualification_name",
        "issuing_organization",
        "certificate_reference",
    )
    readonly_fields = ("id", "created_at")


@admin.register(EmployeeSkill)
class EmployeeSkillAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "skill_name",
        "skill_category",
        "proficiency_level",
        "verified",
    )
    list_filter = ("skill_category", "proficiency_level", "verified")
    search_fields = (
        "employee__employee_code",
        "employee__full_name",
        "skill_name",
    )
    readonly_fields = ("id", "created_at")


@admin.register(EmployeeTraining)
class EmployeeTrainingAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "training_name",
        "provider",
        "completion_date",
        "valid_until",
        "verified",
    )
    list_filter = ("verified", "completion_date", "valid_until")
    search_fields = (
        "employee__employee_code",
        "employee__full_name",
        "training_name",
        "provider",
        "certificate_reference",
    )
    readonly_fields = ("id", "created_at")
