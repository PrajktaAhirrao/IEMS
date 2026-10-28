
from datetime import timedelta

from django.db import migrations
from django.utils import timezone


def grandfather_existing_users(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    now = timezone.now()

    User.objects.using(schema_editor.connection.alias).filter(
        hr_approval_status="PENDING"
    ).update(
        hr_approval_status="APPROVED",
        access_granted_at=now,
        employee_master_due_at=now + timedelta(days=7),
    )


def reverse_grandfathering(apps, schema_editor):
    # Intentionally do not reset approval states automatically.
    # Reversing access-control decisions requires a deliberate recovery plan.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_user_access_granted_at_user_access_revocation_reason_and_more"),
    ]

    operations = [
        migrations.RunPython(
            grandfather_existing_users,
            reverse_grandfathering,
        ),
    ]
