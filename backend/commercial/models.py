
import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from organization.models import LegalEntity


class Enquiry(models.Model):
    class Channel(models.TextChoices):
        PHONE = "PHONE", "Phone"
        EMAIL = "EMAIL", "Email"
        IN_PERSON = "IN_PERSON", "In Person"
        WEBSITE = "WEBSITE", "Website"
        ONLINE_MEETING = "ONLINE_MEETING", "Online Meeting"
        OTHER = "OTHER", "Other"

    class Source(models.TextChoices):
        DIRECT = "DIRECT", "Direct Enquiry"
        REFERRAL = "REFERRAL", "Referral"
        CAMPAIGN = "CAMPAIGN", "Marketing Campaign"
        WEBSITE = "WEBSITE", "Website"
        EXISTING_CUSTOMER = "EXISTING_CUSTOMER", "Existing Customer"
        OTHER = "OTHER", "Other"

    class Intent(models.TextChoices):
        GENERAL_INQUIRY = "GENERAL_INQUIRY", "General Inquiry"
        PRODUCT_REQUIREMENT = "PRODUCT_REQUIREMENT", "Product Requirement"
        QUOTATION_REQUEST = "QUOTATION_REQUEST", "Quotation Request"
        CONTRACTUAL_DISCUSSION = (
            "CONTRACTUAL_DISCUSSION",
            "Contractual Discussion",
        )
        AFTER_SALES = "AFTER_SALES", "After-Sales Support"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        UNDER_REVIEW = "UNDER_REVIEW", "Under Review"
        ROUTED = "ROUTED", "Routed"
        CLOSED = "CLOSED", "Closed"

    class Destination(models.TextChoices):
        FRONT_DESK = "FRONT_DESK", "Commercial Front Desk"
        MARKETING = "MARKETING", "Marketing / Business Development"
        SALES = "SALES", "Sales & Customer Management"
        CONTRACTS = "CONTRACTS", "Contracts & Commercial Management"

    reference_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )

    legal_entity = models.ForeignKey(
        LegalEntity,
        on_delete=models.PROTECT,
        related_name="commercial_enquiries",
    )

    contact_name = models.CharField(max_length=200)
    company_name = models.CharField(max_length=255, blank=True)

    email = models.EmailField(blank=True)
    phone_country_code = models.CharField(max_length=8, blank=True)
    phone_number = models.CharField(max_length=30, blank=True)
    whatsapp_available = models.BooleanField(default=False)

    channel = models.CharField(
        max_length=20,
        choices=Channel.choices,
    )
    source = models.CharField(
        max_length=30,
        choices=Source.choices,
    )
    source_details = models.CharField(max_length=255, blank=True)

    intent = models.CharField(
        max_length=30,
        choices=Intent.choices,
        default=Intent.GENERAL_INQUIRY,
    )

    enquiry_details = models.TextField(blank=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
    )

    routed_destination = models.CharField(
        max_length=20,
        choices=Destination.choices,
        default=Destination.FRONT_DESK,
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_commercial_enquiries",
        null=True,
        blank=True,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_commercial_enquiries",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["legal_entity", "status"],
                name="comm_enq_entity_status_idx",
            ),
            models.Index(
                fields=["legal_entity", "created_at"],
                name="comm_enq_entity_created_idx",
            ),
        ]

    def __str__(self):
        return f"Enquiry {self.reference_id} — {self.contact_name}"
