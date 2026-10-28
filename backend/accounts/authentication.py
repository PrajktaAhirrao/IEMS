
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class HRApprovedTokenAuthentication(TokenAuthentication):
    """
    Preserve DRF's existing Token authentication format while enforcing
    the current HR approval status on every authenticated API request.
    """

    def authenticate_credentials(self, key):
        user, token = super().authenticate_credentials(key)

        if user.hr_approval_status != user.HRApprovalStatus.APPROVED:
            raise AuthenticationFailed(
                "Your account does not currently have HR-approved access."
            )

        return user, token
