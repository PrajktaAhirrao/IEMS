
import argparse
import os
import django

from django.db import transaction

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth import get_user_model
from employees.models import Employee

User = get_user_model()

UPDATES = [
    ("madhura.deshpande@iems.com", "Madhura Deshpande", "Central HR Manager", None),
    ("nikhil.gaikwad@iems.com", "Nikhil Gaikwad", "Plant HR Manager", "PLANT-02"),
    ("pooja.bhosale@iems.com", "Pooja Bhosale", "Plant HR Executive", "PLANT-01"),
    ("shrikant.jadhav@iems.com", "Shrikant Jadhav", "Plant HR Manager", "PLANT-01"),
    ("vaishnavi.shinde@iems.com", "Vaishnavi Shinde", "Plant HR Executive", "PLANT-02"),
]


def build_plan():
    plan = []
    errors = []
    seen = set()

    for email, name, designation, expected_plant in UPDATES:
        user = User.objects.filter(
            email__iexact=email,
            is_active=True,
        ).first()

        if user is None:
            errors.append(f"{email}: active user not found")
            continue

        if user.pk in seen:
            errors.append(f"{email}: duplicate user in update list")
            continue
        seen.add(user.pk)

        employee = Employee.objects.filter(user=user).first()

        if employee is None:
            errors.append(f"{email}: linked Employee record not found")
            continue

        if employee.legal_entity is None or employee.legal_entity.code != "IEMS-MFG":
            errors.append(f"{email}: incorrect or missing legal entity")
            continue

        if expected_plant is None:
            if employee.plant_id is not None:
                errors.append(f"{email}: expected a central, no-plant record")
                continue
        elif (
            employee.plant is None
            or employee.plant.code != expected_plant
        ):
            errors.append(
                f"{email}: expected {expected_plant}, "
                f"found {employee.plant.code if employee.plant else 'None'}"
            )
            continue

        plan.append((
            employee.pk,
            email,
            name,
            designation,
            expected_plant,
        ))

    if not errors and len(plan) != len(UPDATES):
        errors.append("Not all five HR records were validated")

    return plan, errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Apply the validated updates",
    )
    args = parser.parse_args()

    plan, errors = build_plan()

    print("Mode:", "EXECUTE" if args.execute else "DRY RUN")

    if errors:
        print("\nValidation errors:")
        for error in errors:
            print("-", error)
        raise SystemExit(1)

    for _, email, name, designation, plant in plan:
        print(
            f"{'UPDATE' if args.execute else 'WOULD UPDATE'}: "
            f"{email} | {name} | {designation} | plant={plant}"
        )

    print(f"Validated records: {len(plan)}")

    if not args.execute:
        print("Dry run only. No database changes made.")
        return

    with transaction.atomic():
        current_plan, current_errors = build_plan()

        if current_errors or current_plan != plan:
            raise RuntimeError(
                "Validation changed before execution. No updates applied."
            )

        for employee_id, email, name, designation, plant in plan:
            employee = Employee.objects.select_for_update().get(
                pk=employee_id
            )
            employee.full_name = name
            employee.designation = designation
            employee.save(
                update_fields=["full_name", "designation", "updated_at"]
            )

    print(f"Completed successfully. Updated {len(plan)} HR records.")


if __name__ == "__main__":
    main()
