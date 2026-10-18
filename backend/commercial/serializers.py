
from rest_framework import serializers

from organization.models import LegalEntity

from .models import Enquiry


class EnquirySerializer(serializers.ModelSerializer):
    legal_entity_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Enquiry
        fields = [
            "reference_id",
            "legal_entity_id",
            "contact_name",
            "company_name",
            "email",
            "phone_country_code",
            "phone_number",
            "whatsapp_available",
            "channel",
            "source",
            "source_details",
            "intent",
            "enquiry_details",
            "status",
            "routed_destination",
            "assigned_to",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "reference_id",
            "status",
            "routed_destination",
            "assigned_to",
            "created_at",
            "updated_at",
        ]

    def validate_legal_entity_id(self, value):
        request = self.context.get("request")

        if not LegalEntity.objects.filter(
            pk=value,
            is_active=True,
        ).exists():
            raise serializers.ValidationError(
                "The selected legal entity does not exist or is inactive."
            )

        if request is None or not request.user.is_authenticated:
            raise serializers.ValidationError(
                "An authenticated user is required."
            )

        from access_control.models import UserAssignment

        has_access = UserAssignment.objects.filter(
            user=request.user,
            legal_entity_id=value,
            is_active=True,
            role__is_active=True,
            role__role_permissions__permission__code=(
                "commercial.front_desk.access"
            ),
            role__role_permissions__permission__is_active=True,
        ).exists()

        if not has_access:
            raise serializers.ValidationError(
                "You do not have Front Desk access to this legal entity."
            )

        return value

    def create(self, validated_data):
        legal_entity_id = validated_data.pop("legal_entity_id")

        return Enquiry.objects.create(
            legal_entity_id=legal_entity_id,
            created_by=self.context["request"].user,
            **validated_data,
        )
