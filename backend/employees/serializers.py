from rest_framework import serializers

from .models import (
    Employee,
    EmployeeDocument,
    EmployeeEducation,
    EmployeeProfessionalQualification,
    EmployeeSkill,
    EmployeeTraining,
)


class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_code",
            "user",
            "full_name",
            "preferred_name",
            "profile_photo",
            "date_of_birth",
            "date_of_joining",
            "employment_type",
            "employment_status",
            "record_status",
            "legal_entity",
            "plant",
            "department",
            "organizational_unit",
            "designation",
            "reporting_manager",
            "work_location",
            "personal_email",
            "personal_mobile",
            "whatsapp_available",
            "current_address",
            "permanent_address",
            "emergency_contact_name",
            "emergency_contact_relationship",
            "emergency_contact_mobile",
            "created_by",
            "verified_by",
            "verified_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "employee_code",
            "user",
            "record_status",
            "created_by",
            "verified_by",
            "verified_at",
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        instance = self.instance

        legal_entity = attrs.get(
            "legal_entity", instance.legal_entity if instance else None
        )
        plant = attrs.get("plant", instance.plant if instance else None)
        department = attrs.get(
            "department", instance.department if instance else None
        )
        organizational_unit = attrs.get(
            "organizational_unit",
            instance.organizational_unit if instance else None,
        )

        if legal_entity and not legal_entity.is_active:
            raise serializers.ValidationError({
                "legal_entity": "Select an active legal entity."
            })

        if plant:
            if not plant.is_active:
                raise serializers.ValidationError({
                    "plant": "Select an active plant."
                })
            if not legal_entity:
                raise serializers.ValidationError({
                    "legal_entity": (
                        "Select a legal entity before assigning a plant."
                    )
                })
            if plant.legal_entity_id != legal_entity.id:
                raise serializers.ValidationError({
                    "plant": (
                        "The selected plant must belong to the "
                        "selected legal entity."
                    )
                })

        if department and not department.is_active:
            raise serializers.ValidationError({
                "department": "Select an active department."
            })

        if organizational_unit:
            if not organizational_unit.is_active:
                raise serializers.ValidationError({
                    "organizational_unit": (
                        "Select an active organizational unit."
                    )
                })
            if (
                legal_entity
                and organizational_unit.legal_entity_id != legal_entity.id
            ):
                raise serializers.ValidationError({
                    "organizational_unit": (
                        "The organizational unit must belong to "
                        "the selected legal entity."
                    )
                })
            if (
                department
                and organizational_unit.department_id != department.id
            ):
                raise serializers.ValidationError({
                    "organizational_unit": (
                        "The organizational unit must match the "
                        "selected department."
                    )
                })
            if (
                plant
                and organizational_unit.scope_type == "PLANT"
                and organizational_unit.plant_id != plant.id
                and not organizational_unit.served_plants.filter(
                    pk=plant.id
                ).exists()
            ):
                raise serializers.ValidationError({
                    "organizational_unit": (
                        "The organizational unit is not assigned "
                        "to the selected plant."
                    )
                })

        if department and not department.functional_area.is_active:
            raise serializers.ValidationError({
                "department": (
                    "The department's functional area is inactive."
                )
            })

        return attrs


class EmployeeDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeDocument
        fields = [
            "id",
            "employee",
            "document_type",
            "holder_name",
            "document_number",
            "file",
            "issued_by",
            "expiry_date",
            "verification_status",
            "verified_by",
            "verified_at",
            "created_by",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "verification_status",
            "verified_by",
            "verified_at",
            "created_by",
            "created_at",
        ]


class EmployeeEducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeEducation
        fields = [
            "id",
            "employee",
            "education_level",
            "qualification",
            "institution",
            "board_or_university",
            "passing_year",
            "result_or_grade",
            "proof_document",
            "verified",
            "verified_by",
            "verified_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "verified",
            "verified_by",
            "verified_at",
            "created_at",
        ]


class EmployeeProfessionalQualificationSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = EmployeeProfessionalQualification
        fields = [
            "id",
            "employee",
            "qualification_name",
            "issuing_organization",
            "certificate_reference",
            "issue_date",
            "valid_until",
            "proof_document",
            "verified",
            "verified_by",
            "verified_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "verified",
            "verified_by",
            "verified_at",
            "created_at",
        ]


class EmployeeSkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeSkill
        fields = [
            "id",
            "employee",
            "skill_name",
            "skill_category",
            "proficiency_level",
            "notes",
            "verified",
            "verified_by",
            "verified_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "verified",
            "verified_by",
            "verified_at",
            "created_at",
        ]


class EmployeeTrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeTraining
        fields = [
            "id",
            "employee",
            "training_name",
            "provider",
            "completion_date",
            "certificate_reference",
            "valid_until",
            "certificate_file",
            "verified",
            "verified_by",
            "verified_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "verified",
            "verified_by",
            "verified_at",
            "created_at",
        ]
