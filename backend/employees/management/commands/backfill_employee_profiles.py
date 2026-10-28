
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from access_control.models import UserAssignment
from employees.models import Employee
from organization.models import LegalEntity, Plant


ENTITY_CODE = "IEMS-MFG"
CENTRAL_HR_EMAIL = "madhura.deshpande@iems.com"

EXPECTED_PLANT_ROLES = {
    "PLANT_HR_MANAGER",
    "PLANT_HR_EXECUTIVE",
}


class Command(BaseCommand):
    help = (
        "Dry-run or create missing draft Employee profiles for active "
        "accounts assigned to IEMS-MFG."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--execute",
            action="store_true",
            help="Write records. Without this flag, the command is read-only.",
        )

    def handle(self, *args, **options):
        execute = options["execute"]
        User = get_user_model()
        errors = []
        plans = []

        entity = LegalEntity.objects.filter(
            code=ENTITY_CODE,
            is_active=True,
        ).first()

        if entity is None:
            raise CommandError(
                f"Active legal entity {ENTITY_CODE!r} was not found."
            )

        actor = User.objects.filter(
            email__iexact=CENTRAL_HR_EMAIL,
            is_active=True,
        ).first()

        if actor is None:
            raise CommandError("The active Central HR audit actor was not found.")

        actor_assignments = UserAssignment.objects.filter(
            user=actor,
            legal_entity=entity,
            is_active=True,
            role__code="CENTRAL_HR",
            role__is_active=True,
            role__functional_area__code="CORPORATE_GOVERNANCE",
            role__role_permissions__permission__code=(
                "employees.employee_master.manage"
            ),
            role__role_permissions__permission__is_active=True,
            plant__isnull=True,
        ).distinct()

        if not actor_assignments.exists():
            raise CommandError(
                "Central HR actor lacks an active entity-wide "
                "Employee Master manage assignment."
            )

        users = User.objects.filter(is_active=True).order_by("pk")

        for user in users:
            assignments = list(
                UserAssignment.objects.filter(
                    user=user,
                    is_active=True,
                    legal_entity=entity,
                    role__is_active=True,
                ).select_related(
                    "role",
                    "legal_entity",
                    "plant",
                    "role__functional_area",
                ).distinct()
            )

            # Only backfill accounts whose active assignments are all
            # represented by one unambiguous assignment in this entity.
            if len(assignments) != 1:
                errors.append(
                    f"{user.email}: expected exactly one active assignment "
                    f"for {ENTITY_CODE}; found {len(assignments)}."
                )
                continue

            assignment = assignments[0]

            # Fail closed if the role belongs to an unexpected functional area.
            if assignment.role.functional_area.code not in {
                "COMMERCIAL",
                "CORPORATE_GOVERNANCE",
            }:
                errors.append(
                    f"{user.email}: unexpected functional area "
                    f"{assignment.role.functional_area.code!r}."
                )
                continue

            plant = assignment.plant

            if plant is not None:
                if (
                    not plant.is_active
                    or plant.legal_entity_id != entity.pk
                ):
                    errors.append(
                        f"{user.email}: assigned plant is inactive or "
                        "belongs to another legal entity."
                    )
                    continue

            # Plant HR roles must have an explicit plant.
            if assignment.role.code in EXPECTED_PLANT_ROLES and plant is None:
                errors.append(
                    f"{user.email}: plant HR role has no assigned plant."
                )
                continue

            # Non-plant HR and commercial users are expected to be
            # entity-wide in this backfill.
            if (
                assignment.role.code not in EXPECTED_PLANT_ROLES
                and plant is not None
            ):
                errors.append(
                    f"{user.email}: unexpected plant assignment for "
                    f"role {assignment.role.code}."
                )
                continue

            existing = Employee.objects.filter(user=user).first()

            if existing is not None:
                if (
                    existing.legal_entity_id != entity.pk
                    or existing.plant_id != (
                        plant.pk if plant is not None else None
                    )
                ):
                    errors.append(
                        f"{user.email}: existing Employee record has a "
                        "different legal entity or plant; manual review required."
                    )
                else:
                    plans.append((user, plant, "SKIP", "Already linked"))
                continue

            plans.append((user, plant, "CREATE", "Missing Employee record"))

        self.stdout.write(f"Mode: {'EXECUTE' if execute else 'DRY RUN'}")
        self.stdout.write(f"Active accounts inspected: {users.count()}")

        for user, plant, action, reason in plans:
            plant_code = plant.code if plant else "ENTITY-WIDE"
            self.stdout.write(
                f"{action}: {user.email} | "
                f"entity={entity.code} | plant={plant_code} | {reason}"
            )

        if errors:
            self.stdout.write(self.style.ERROR(
                f"Validation errors: {len(errors)}"
            ))
            for error in errors:
                self.stdout.write(self.style.ERROR(f"- {error}"))
            raise CommandError(
                "Validation failed. No Employee records were created."
            )

        create_count = sum(action == "CREATE" for _, _, action, _ in plans)
        skip_count = sum(action == "SKIP" for _, _, action, _ in plans)

        self.stdout.write(f"Would create: {create_count}")
        self.stdout.write(f"Would skip: {skip_count}")

        if not execute:
            self.stdout.write(
                self.style.WARNING(
                    "Dry run only. No database records were changed."
                )
            )
            return

        with transaction.atomic():
            # Recheck the account/profile state while writing to avoid
            # blindly acting on stale dry-run results.
            for user, plant, action, _ in plans:
                if action != "CREATE":
                    continue

                if Employee.objects.filter(user=user).exists():
                    raise CommandError(
                        f"{user.email} acquired an Employee record after "
                        "validation. Transaction aborted."
                    )

                Employee.objects.create(
                    user=user,
                    legal_entity=entity,
                    plant=plant,
                    record_status=Employee.RecordStatus.DRAFT,
                    created_by=actor,
                )

        self.stdout.write(self.style.SUCCESS(
            f"Backfill complete. Created {create_count}; skipped {skip_count}."
        ))
