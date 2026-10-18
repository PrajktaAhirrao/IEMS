
from django.contrib import admin

from .models import Enquiry


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "reference_id",
        "contact_name",
        "company_name",
        "channel",
        "intent",
        "status",
        "routed_destination",
        "legal_entity",
        "created_at",
    )

    list_filter = (
        "status",
        "channel",
        "source",
        "intent",
        "routed_destination",
        "legal_entity",
    )

    search_fields = (
        "contact_name",
        "company_name",
        "email",
        "phone_number",
        "reference_id",
    )

    readonly_fields = (
        "reference_id",
        "created_at",
        "updated_at",
    )

    ordering = ("-created_at",)

    list_per_page = 25
