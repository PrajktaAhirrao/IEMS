
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from employees.models import Employee
from organization.models import (
    BusinessGroup,
    DepartmentDefinition,
    Enterprise,
    FunctionalArea,
    LegalEntity,
    Plant,
)


class EmployeeModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            username="employee_test_hr",
            password="test-only-password",
        )

        enterprise = Enterprise.objects.create(
            code="TEST-ENT",
            name="Test Enterprise",
        )
        group = BusinessGroup.objects.create(
            enterprise=enterprise,
            code="TEST-GRP",
            name="Test Group",
        )
        cls.legal_entity = LegalEntity.objects.create(
            business_group=group,
            code="TEST-LE",
            legal_name="Test Legal Entity",
            display_name="Test Legal Entity",
        )
        cls.plant = Plant.objects.create(
            legal_entity=cls.legal_entity,
            code="TEST-PLANT",
            name="Test Plant",
        )
        area = FunctionalArea.objects.create(
            code="TEST-HR",
            name="Test HR",
        )
        cls.department = DepartmentDefinition.objects.create(
            functional_area=area,
            code="TEST-DEPT",
            name="Test Department",
            scope_type=DepartmentDefinition.ScopeType.PLANT,
        )

    def make_employee(self, **overrides):
        data = {
            "employee_code": "TEST-EMP-001",
            "full_name": "Test Employee",
            "date_of_joining": date(2026, 1, 1),
            "employment_type": Employee.EmploymentType.PERMANENT,
            "legal_entity": self.legal_entity,
            "plant": self.plant,
            "department": self.department,
            "designation": "Test Engineer",
            "created_by": self.user,
        }
        data.update(overrides)
        return Employee(**data)

    def test_draft_employee_can_have_incomplete_details(self):
        employee = self.make_employee(
            full_name="",
            date_of_joining=None,
            employment_type="",
            department=None,
            designation="",
        )

        employee.full_clean()

    def test_verified_employee_requires_verifier(self):
        employee = self.make_employee(
            record_status=Employee.RecordStatus.VERIFIED,
        )

        with self.assertRaises(ValidationError) as context:
            employee.full_clean()

        self.assertIn("verified_by", context.exception.message_dict)
        self.assertIn("verified_at", context.exception.message_dict)

    def test_employee_plant_must_belong_to_legal_entity(self):
        other_enterprise = Enterprise.objects.create(
            code="TEST-ENT-2",
            name="Other Test Enterprise",
        )
        other_group = BusinessGroup.objects.create(
            enterprise=other_enterprise,
            code="TEST-GRP-2",
            name="Other Test Group",
        )
        other_entity = LegalEntity.objects.create(
            business_group=other_group,
            code="TEST-LE-2",
            legal_name="Other Legal Entity",
            display_name="Other Legal Entity",
        )
        other_plant = Plant.objects.create(
            legal_entity=other_entity,
            code="TEST-PLANT-2",
            name="Other Plant",
        )

        employee = self.make_employee(plant=other_plant)

        with self.assertRaises(ValidationError) as context:
            employee.full_clean()

        self.assertIn("plant", context.exception.message_dict)

    def test_employee_cannot_report_to_themselves(self):
        employee = self.make_employee()
        employee.pk = "00000000-0000-0000-0000-000000000001"
        employee.id = employee.pk
        employee.reporting_manager_id = employee.pk

        with self.assertRaises(ValidationError) as context:
            employee.full_clean()

        self.assertIn(
            "reporting_manager",
            context.exception.message_dict,
        )
