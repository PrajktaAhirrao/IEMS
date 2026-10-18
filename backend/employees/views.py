
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
        legal_entity_id = request.query_params.get("legal_entity_id")

        if not legal_entity_id or not str(legal_entity_id).isdigit():
            raise ValidationError({
                "legal_entity_id": "A valid legal entity is required."
            })

        all_plants, plant_ids = get_authorized_plant_ids(
            request.user,
            int(legal_entity_id),
            "employees.employee_master.view",
        )

        employees = Employee.objects.filter(
            legal_entity_id=legal_entity_id,
        )

        if not all_plants:
            employees = employees.filter(plant_id__in=plant_ids)

        requested_plant_id = request.query_params.get("plant_id")

        if requested_plant_id:
            if not str(requested_plant_id).isdigit():
                raise ValidationError({
                    "plant_id": "A valid plant ID is required."
                })

            if not can_access_plant(
                request.user,
                int(legal_entity_id),
                int(requested_plant_id),
                "employees.employee_master.view",
            ):
                raise ValidationError({
                    "plant_id": "You are not authorized to access this plant."
                })

            employees = employees.filter(plant_id=requested_plant_id)

        employees = employees.select_related(
            "legal_entity",
            "plant",
            "department",
            "organizational_unit",
            "reporting_manager",
            "user",
            "created_by",
        )

        return Response(EmployeeSerializer(employees, many=True).data)

    def post(self, request):
        legal_entity_id = (
            request.data.get("legal_entity_id")
            or request.data.get("legal_entity")
        )

        if not legal_entity_id or not str(legal_entity_id).isdigit():
            raise ValidationError({
                "legal_entity": "A valid legal entity is required."
            })

        legal_entity = LegalEntity.objects.filter(
            pk=legal_entity_id,
            is_active=True,
        ).first()

        if not legal_entity:
            raise ValidationError({
                "legal_entity": (
                    "The selected legal entity is inactive or does not exist."
                )
            })

        plant_id = request.data.get("plant_id") or request.data.get("plant")

        if not plant_id or not str(plant_id).isdigit():
            raise ValidationError({
                "plant": "A valid plant is required to create an employee."
            })

        plant = Plant.objects.filter(
            pk=plant_id,
            legal_entity=legal_entity,
            is_active=True,
        ).first()

        if not plant:
            raise ValidationError({
                "plant": (
                    "The selected plant is inactive, does not exist, "
                    "or does not belong to this legal entity."
                )
            })

        if not can_access_plant(
            request.user,
            legal_entity.pk,
            plant.pk,
            "employees.employee_master.manage",
        ):
            raise ValidationError({
                "plant": (
                    "You are not authorized to create employees at this plant."
                )
            })

        data = request.data.copy()
        data["legal_entity"] = legal_entity.pk
        data["plant"] = plant.pk

        serializer = EmployeeSerializer(
            data=data,
            context={"request": request},
        )
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
        legal_entity_id = request.query_params.get("legal_entity_id")

        if not legal_entity_id or not str(legal_entity_id).isdigit():
            raise ValidationError({
                "legal_entity_id": "A valid legal entity is required."
            })

        employee = Employee.objects.filter(
            pk=employee_id,
            legal_entity_id=legal_entity_id,
        ).select_related(
            "legal_entity",
            "plant",
            "department",
            "organizational_unit",
            "reporting_manager",
            "created_by",
        ).first()

        if employee is None:
            raise NotFound("Employee not found.")

        if not employee.plant_id or not can_access_plant(
            request.user,
            int(legal_entity_id),
            employee.plant_id,
            permission_code,
        ):
            raise NotFound("Employee not found.")

        return employee

    def get(self, request, employee_id):
        employee = self.get_employee(
            request,
            employee_id,
            "employees.employee_master.view",
        )
        return Response(EmployeeSerializer(employee).data)

    def patch(self, request, employee_id):
        employee = self.get_employee(
            request,
            employee_id,
            "employees.employee_master.manage",
        )

        data = request.data.copy()
        data.pop("record_status", None)
        data.pop("verified_by", None)
        data.pop("verified_at", None)
        data.pop("created_by", None)
        data.pop("user", None)

        serializer = EmployeeSerializer(
            employee,
            data=data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()

        return Response(EmployeeSerializer(employee).data)

    def put(self, request, employee_id):
        raise ValidationError(
            "Full replacement is disabled. Use PATCH to update selected fields."
        )
