
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    class HRApprovalStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        REVOKED = "REVOKED", "Revoked"

    email = models.EmailField(unique=True)

    hr_approval_status = models.CharField(
        max_length=20,
        choices=HRApprovalStatus.choices,
        default=HRApprovalStatus.PENDING,
        db_index=True,
    )
    hr_approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_approved_users",
    )
    hr_approved_at = models.DateTimeField(null=True, blank=True)
    access_granted_at = models.DateTimeField(null=True, blank=True)
    employee_master_due_at = models.DateTimeField(null=True, blank=True)
    employee_master_overdue_notified_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    access_revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_revoked_users",
    )
    access_revoked_at = models.DateTimeField(null=True, blank=True)
    access_revocation_reason = models.TextField(blank=True, default="")

    def grant_hr_access(self, approved_by):
        now = timezone.now()
        self.hr_approval_status = self.HRApprovalStatus.APPROVED
        self.hr_approved_by = approved_by
        self.hr_approved_at = now
        self.access_granted_at = now
        self.employee_master_due_at = now + timezone.timedelta(days=7)
        self.employee_master_overdue_notified_at = None
        self.access_revoked_by = None
        self.access_revoked_at = None
        self.access_revocation_reason = ""
        self.save(update_fields=[
            "hr_approval_status",
            "hr_approved_by",
            "hr_approved_at",
            "access_granted_at",
            "employee_master_due_at",
            "employee_master_overdue_notified_at",
            "access_revoked_by",
            "access_revoked_at",
            "access_revocation_reason",
        ])

    def revoke_hr_access(self, revoked_by, reason):
        self.hr_approval_status = self.HRApprovalStatus.REVOKED
        self.access_revoked_by = revoked_by
        self.access_revoked_at = timezone.now()
        self.access_revocation_reason = reason
        self.save(update_fields=[
            "hr_approval_status",
            "access_revoked_by",
            "access_revoked_at",
            "access_revocation_reason",
        ])

    def __str__(self):
        return self.email or self.username
