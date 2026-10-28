from django.contrib.auth import authenticate, get_user_model

from rest_framework import status
from .authentication import HRApprovedTokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer
from django.db import transaction
from rest_framework.exceptions import PermissionDenied

from access_control.models import UserAccessEvent, UserAssignment
from employees.scope import can_access_plant, get_hr_assignments


User = get_user_model()


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"].strip().lower()
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = authenticate(
            request=request,
            username=user.username,
            password=password,
        )

        if user is None:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {"detail": "This account is inactive."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if user.hr_approval_status != User.HRApprovalStatus.APPROVED:
            return Response(
                {"detail": "This account has not been approved for access by HR."},
                status=status.HTTP_403_FORBIDDEN,
            )

        token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "token": token.key,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                },
            },
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    authentication_classes = [HRApprovedTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        assignments = (
            user.assignments.filter(
                is_active=True,
                role__is_active=True,
            )
            .select_related(
                "role",
                "role__functional_area",
                "role__department",
                "legal_entity",
                "plant",
                "organizational_unit",
            )
            .prefetch_related(
                "role__role_permissions__permission"
            )
        )

        assignment_data = []
        effective_permissions = set()

        for assignment in assignments:
            permissions = list(
                assignment.role.role_permissions.filter(
                    permission__is_active=True,
                ).values_list(
                    "permission__code",
                    flat=True,
                )
            )

            effective_permissions.update(permissions)

            assignment_data.append(
                {
                    "role": {
                        "id": assignment.role_id,
                        "code": assignment.role.code,
                        "name": assignment.role.name,
                        "scope_level": assignment.role.scope_level,
                    },
                    "legal_entity_id": assignment.legal_entity_id,
                    "plant_id": assignment.plant_id,
                    "organizational_unit_id": (
                        assignment.organizational_unit_id
                    ),
                    "is_primary": assignment.is_primary,
                    "permissions": permissions,
                }
            )

        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_staff": user.is_staff,
                    "is_superuser": user.is_superuser,
                },
                "assignments": assignment_data,
                "permissions": sorted(effective_permissions),
            },
            status=status.HTTP_200_OK,
        )


class UserAccessManagementView(APIView):
    authentication_classes = [HRApprovedTokenAuthentication]
    permission_classes = [IsAuthenticated]

    permission_code = "employees.hr_operations.approve"

    def post(self, request, user_id, action):
        if action not in {"approve", "reject", "revoke"}:
            return Response(
                {"detail": "Unsupported access action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user_id == request.user.id:
            return Response(
                {"detail": "You cannot change your own access approval."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        legal_entity_value = request.data.get("legal_entity_id")
        plant_value = request.data.get("plant_id")

        if (
            legal_entity_value is None
            or not str(legal_entity_value).isdigit()
            or int(legal_entity_value) <= 0
        ):
            return Response(
                {"legal_entity_id": "A valid legal entity is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        legal_entity_id = int(legal_entity_value)
        plant_id = None

        if plant_value not in (None, ""):
            if not str(plant_value).isdigit() or int(plant_value) <= 0:
                return Response(
                    {"plant_id": "A valid plant ID is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            plant_id = int(plant_value)

        reason = str(request.data.get("reason", "")).strip()

        if action in {"reject", "revoke"} and not reason:
            return Response(
                {"reason": "A reason is required for this action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        messages = {
            "approve": "User access approved successfully.",
            "reject": "User access rejected successfully.",
            "revoke": "User access revoked successfully.",
        }

        with transaction.atomic():
            # Lock the target before checking or changing its status.
            target = (
                User.objects.select_for_update()
                .filter(pk=user_id)
                .first()
            )

            if target is None:
                return Response(
                    {"detail": "User not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Revalidate the actor's authority within the transaction.
            actor_assignments = get_hr_assignments(
                request.user,
                legal_entity_id,
                self.permission_code,
            )

            if not actor_assignments.exists():
                raise PermissionDenied(
                    "You are not authorized to manage access "
                    "in this legal entity."
                )

            has_entity_wide_access = actor_assignments.filter(
                role__code="CENTRAL_HR",
                plant__isnull=True,
            ).exists()

            if has_entity_wide_access:
                # A user-wide approval change must not affect assignments
                # belonging to another legal entity.
                if plant_id is not None:
                    if not can_access_plant(
                        request.user,
                        legal_entity_id,
                        plant_id,
                        self.permission_code,
                    ):
                        raise PermissionDenied(
                            "You are not authorized to manage access "
                            "for this plant."
                        )
            else:
                if plant_id is None:
                    return Response(
                        {"plant_id": "A valid plant ID is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if not can_access_plant(
                    request.user,
                    legal_entity_id,
                    plant_id,
                    self.permission_code,
                ):
                    raise PermissionDenied(
                        "You are not authorized to manage access "
                        "for this plant."
                    )

            # Lock existing assignments and recheck the scope while
            # the target user is locked.
            target_assignments = list(
                UserAssignment.objects.select_for_update().filter(
                    user=target,
                    is_active=True,
                    role__is_active=True,
                )
            )

            if has_entity_wide_access:
                if any(
                    assignment.legal_entity_id != legal_entity_id
                    for assignment in target_assignments
                ):
                    raise PermissionDenied(
                        "This user has assignments outside your "
                        "legal-entity scope."
                    )
            else:
                if not target_assignments:
                    raise PermissionDenied(
                        "Only Central HR can manage access for a user "
                        "without active role assignments."
                    )

                if any(
                    assignment.legal_entity_id != legal_entity_id
                    or assignment.plant_id != plant_id
                    for assignment in target_assignments
                ):
                    raise PermissionDenied(
                        "This user has assignments outside your plant scope."
                    )

            previous_status = target.hr_approval_status

            if action == "approve":
                if previous_status == User.HRApprovalStatus.APPROVED:
                    return Response(
                        {"detail": "This user is already approved."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                target.grant_hr_access(request.user)

                event_type = (
                    UserAccessEvent.EventType.RESTORED
                    if previous_status == User.HRApprovalStatus.REVOKED
                    else UserAccessEvent.EventType.APPROVED
                )

            elif action == "reject":
                target.hr_approval_status = User.HRApprovalStatus.REJECTED
                target.save(update_fields=["hr_approval_status"])
                event_type = UserAccessEvent.EventType.REJECTED

            else:
                if previous_status != User.HRApprovalStatus.APPROVED:
                    return Response(
                        {"detail": "Only approved accounts can be revoked."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                target.revoke_hr_access(request.user, reason)
                event_type = UserAccessEvent.EventType.REVOKED

            # Rejection and revocation invalidate existing DRF tokens.
            if action in {"reject", "revoke"}:
                Token.objects.filter(user=target).delete()

            UserAccessEvent.objects.create(
                user=target,
                actor=request.user,
                event_type=event_type,
                reason=reason,
            )

        return Response(
            {
                "detail": messages[action],
                "user_id": target.pk,
                "hr_approval_status": target.hr_approval_status,
            },
            status=status.HTTP_200_OK,
        )
