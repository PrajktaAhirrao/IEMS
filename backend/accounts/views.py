from django.contrib.auth import authenticate, get_user_model

from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer


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
    authentication_classes = [TokenAuthentication]
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
