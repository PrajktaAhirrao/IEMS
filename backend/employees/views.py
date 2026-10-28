
from django.db import transaction
from django.db.models import Q

from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from organization.models import LegalEntity, Plant

from .models import Employee
from .permissions import HasEmployeeMasterPermission
from .scope import can_access_plant, get_authorized_plant_ids
from .serializers import EmployeeSerializer


class EmployeeListCreateView(APIView):
    permission_classes = [HasEmployeeMasterPermission]

    def get_permissions(self):
        if self.request.method == "GET":
            self.required_permission = "employees.employee_master.view"
        elif self.request.method == "POST":
            self.required_permission = "employees.employee_master.manage"
        else:
            self.required_permission = None
        return super().get_permissions()

    def get(self, request):
        entity_value = request.query_params.get("legal_entity_id")
        if not entity_value or not str(entity_value).isdigit():
            raise ValidationError({
                "legal_entity_id": "A valid legal entity is required."
            })

        entity_id = int(entity_value)
        all_plants, plant_ids = get_authorized_plant_ids(
            request.user, entity_id, "employees.employee_master.view"
        )

        employees = Employee.objects.filter(legal_entity_id=entity_id)

        if not all_plants:
            # A plant-scoped user must not see central records or
            # records belonging to another plant.
            employees = employees.filter(plant_id__in=plant_ids)

        requested_plant = request.query_params.get("plant_id")
        if requested_plant:
            if not str(requested_plant).isdigit():
                raise ValidationError({"plant_id": "A valid plant ID is required."})
            requested_plant_id = int(requested_plant)
            if not can_access_plant(
                request.user, entity_id, requested_plant_id,
                "employees.employee_master.view",
            ):
                raise ValidationError({
                    "plant_id": "You are not authorized to access this plant."
                })
            employees = employees.filter(plant_id=requested_plant_id)

        employees = employees.select_related(
            "legal_entity", "plant", "department", "organizational_unit",
            "reporting_manager", "user", "created_by",
        )
        return Response(EmployeeSerializer(employees, many=True).data)

    def post(self, request):
        entity_value = request.data.get("legal_entity_id") or request.data.get("legal_entity")
        if not entity_value or not str(entity_value).isdigit():
            raise ValidationError({"legal_entity": "A valid legal entity is required."})

        entity = LegalEntity.objects.filter(
            pk=int(entity_value), is_active=True
        ).first()
        if entity is None:
            raise ValidationError({
                "legal_entity": "The legal entity is inactive or does not exist."
            })

        plant_value = request.data.get("plant_id") or request.data.get("plant")
        plant = None

        if plant_value not in (None, ""):
            if not str(plant_value).isdigit():
                raise ValidationError({"plant": "A valid plant ID is required."})
            plant = Plant.objects.filter(
                pk=int(plant_value), legal_entity=entity, is_active=True
            ).first()
            if plant is None:
                raise ValidationError({
                    "plant": "The plant is inactive, does not exist, or belongs to another legal entity."
                })

        if plant:
            allowed = can_access_plant(
                request.user, entity.pk, plant.pk,
                "employees.employee_master.manage",
            )
        else:
            # A no-plant record is a central record. Only an assignment
            # with entity-wide authority may create it.
            all_plants, _ = get_authorized_plant_ids(
                request.user, entity.pk, "employees.employee_master.manage"
            )
            allowed = all_plants

        if not allowed:
            raise ValidationError({
                "plant": "You are not authorized to create an employee at this scope."
            })

        data = request.data.copy()
        data["legal_entity"] = entity.pk
        data["plant"] = plant.pk if plant else None
        data.pop("user", None)
        data.pop("record_status", None)
        data.pop("created_by", None)
        data.pop("verified_by", None)
        data.pop("verified_at", None)

        serializer = EmployeeSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        employee = serializer.save(created_by=request.user)

        return Response(
            EmployeeSerializer(employee).data,
            status=status.HTTP_201_CREATED,
        )


class EmployeeDetailView(APIView):
    permission_classes = [HasEmployeeMasterPermission]

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            self.required_permission = "employees.employee_master.view"
        elif self.request.method in ("PATCH", "PUT"):
            self.required_permission = "employees.employee_master.manage"
        else:
            self.required_permission = None
        return super().get_permissions()

    def get_employee(self, request, employee_id, permission_code):
        entity_value = request.query_params.get("legal_entity_id")
        if not entity_value or not str(entity_value).isdigit():
            raise ValidationError({
                "legal_entity_id": "A valid legal entity is required."
            })

        entity_id = int(entity_value)
        employee = Employee.objects.filter(
            pk=employee_id, legal_entity_id=entity_id
        ).select_related("plant", "legal_entity", "user", "created_by").first()

        if employee is None:
            raise NotFound("Employee not found.")

        if employee.plant_id:
            allowed = can_access_plant(
                request.user, entity_id, employee.plant_id, permission_code
            )
        else:
            all_plants, _ = get_authorized_plant_ids(
                request.user, entity_id, permission_code
            )
            allowed = all_plants

        if not allowed:
            raise NotFound("Employee not found.")

        return employee

    def get(self, request, employee_id):
        employee = self.get_employee(
            request, employee_id, "employees.employee_master.view"
        )
        return Response(EmployeeSerializer(employee).data)

    def patch(self, request, employee_id):
        employee = self.get_employee(
            request, employee_id, "employees.employee_master.manage"
        )
        data = request.data.copy()
        for field in (
            "record_status", "verified_by", "verified_at", "created_by", "user"
        ):
            data.pop(field, None)

        serializer = EmployeeSerializer(
            employee, data=data, partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()
        return Response(EmployeeSerializer(employee).data)

    def put(self, request, employee_id):
        raise ValidationError(
            "Full replacement is disabled. Use PATCH to update selected fields."
        )
