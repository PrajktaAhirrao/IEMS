from django.urls import path

from .views import (
    CurrentUserView,
    LoginView,
    UserAccessManagementView,
)

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path(
        "access/<int:user_id>/<str:action>/",
        UserAccessManagementView.as_view(),
        name="user-access-management",
    ),
]