
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Enquiry
from .permissions import HasCommercialPermission
from .serializers import EnquirySerializer


class EnquiryListCreateView(APIView):
    permission_classes = [HasCommercialPermission]
    required_permission = "commercial.front_desk.access"

    def get(self, request):
        legal_entity_id = request.query_params.get("legal_entity_id")

        enquiries = Enquiry.objects.filter(
            legal_entity_id=legal_entity_id,
        ).select_related(
            "legal_entity",
            "created_by",
            "assigned_to",
        )

        serializer = EnquirySerializer(
            enquiries,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        serializer = EnquirySerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        enquiry = serializer.save()

        return Response(
            EnquirySerializer(
                enquiry,
                context={"request": request},
            ).data,
            status=status.HTTP_201_CREATED,
        )
