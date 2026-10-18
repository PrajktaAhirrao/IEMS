
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from access_control.models import (
    Permission,
    Role,
    RolePermission,
    UserAssignment,
)
from employees.models import Employee
from organization.models import (
    BusinessGroup,
    DepartmentDefinition,
    Enterprise,
    FunctionalArea,
    LegalEntity,
    OrganizationalGroup,
    Plant,
)


class EmployeeAccessTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()

        cls.central_user = User.objects.create_user(
            username="central_hr_test",
            email="central_hr_test@example.com",
            password="test-password",
        )
        cls.plant_user = User.objects.create_user(
            username="plant_hr_test",
            email="plant_hr_test@example.com",
            password="test-password",
        )
        cls.unassigned_user = User.objects.create_user(
            username="unassigned_test",
            email="unassigned_test@example.com",
            password="test-password",
        )

        enterprise = Enterprise.objects.create(
            code="ACCESS-ENT",
            name="Access Test Enterprise",
        )
        group = BusinessGroup.objects.create(
            enterprise=enterprise,
            code="ACCESS-GRP",
            name="Access Test Group",
        )
        cls.entity = LegalEntity.objects.create(
            business_group=group,
            code="ACCESS-LE",
            legal_name="Access Test Entity",
            display_name="Access Test Entity",
        )
        cls.plant1 = Plant.objects.create(
            legal_entity=cls.entity,
            code="ACCESS-P1",
            name="Access Plant 1",
        )
        cls.plant2 = Plant.objects.create(
            legal_entity=cls.entity,
            code="ACCESS-P2",
            name="Access Plant 2",
        )

        org_group = OrganizationalGroup.objects.create(
            code="ACCESS-ORG",
            name="Access Test Organization",
        )
        cls.hr_area = FunctionalArea.objects.create(
            group=org_group,
            code="ACCESS-HR",
            name="Access Test HR",
        )
        cls.department = DepartmentDefinition.objects.create(
            functional_area=cls.hr_area,
            code="ACCESS-DEPT",
            name="Access Test Department",
            scope_type=DepartmentDefinition.ScopeType.PLANT,
        )

        # Reuse existing permission records.
        cls.view_permission, _ = Permission.objects.get_or_create(
            code="employees.employee_master.view",
            defaults={"name": "View Employee Master"},
        )
        cls.manage_permission, _ = Permission.objects.get_or_create(
            code="employees.employee_master.manage",
            defaults={"name": "Manage Employee Master"},
        )

        # Reuse the actual role definitions so scope.py recognizes them.
        cls.central_role = Role.objects.get(code="CENTRAL_HR")
        cls.plant_role = Role.objects.get(code="PLANT_HR_MANAGER")

        # Avoid duplicate role-permission records.
        for role in (cls.central_role, cls.plant_role):
            for permission in (
                cls.view_permission,
                cls.manage_permission,
            ):
                RolePermission.objects.get_or_create(
                    role=role,
                    permission=permission,
                )

        UserAssignment.objects.create(
            user=cls.central_user,
            role=cls.central_role,
            legal_entity=cls.entity,
            plant=None,
        )
        UserAssignment.objects.create(
            user=cls.plant_user,
            role=cls.plant_role,
            legal_entity=cls.entity,
            plant=cls.plant1,
        )

        cls.employee = Employee.objects.create(
            employee_code="ACCESS-EMP-1",
            full_name="Plant One Employee",
            date_of_joining=date(2026, 1, 1),
            employment_type=Employee.EmploymentType.PERMANENT,
            legal_entity=cls.entity,
            plant=cls.plant1,
            department=cls.department,
            designation="Test Engineer",
            created_by=cls.central_user,
        )

    def setUp(self):
        self.client = APIClient()
        self.url = "/api/employees/"

    def test_central_hr_can_list_entity_employees(self):
        self.client.force_authenticate(user=self.central_user)

        response = self.client.get(
            self.url,
            {"legal_entity_id": self.entity.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_plant_hr_can_list_assigned_plant(self):
        self.client.force_authenticate(user=self.plant_user)

        response = self.client.get(
            self.url,
            {
                "legal_entity_id": self.entity.pk,
                "plant_id": self.plant1.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_plant_hr_cannot_list_another_plant(self):
        self.client.force_authenticate(user=self.plant_user)

        response = self.client.get(
            self.url,
            {
                "legal_entity_id": self.entity.pk,
                "plant_id": self.plant2.pk,
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_unassigned_user_cannot_list_employees(self):
        self.client.force_authenticate(user=self.unassigned_user)

        response = self.client.get(
            self.url,
            {"legal_entity_id": self.entity.pk},
        )

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_cannot_list_employees(self):
        response = self.client.get(
            self.url,
            {"legal_entity_id": self.entity.pk},
        )

        self.assertEqual(response.status_code, 401)
