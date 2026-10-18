
from django.urls import path

from .views import EnquiryListCreateView

urlpatterns = [
    path(
        "enquiries/",
        EnquiryListCreateView.as_view(),
        name="enquiry-list-create",
    ),
]
