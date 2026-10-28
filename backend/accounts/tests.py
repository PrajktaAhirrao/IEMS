from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.test import APIClient, APIRequestFactory

from accounts.authentication import HRApprovedTokenAuthentication
from accounts.models import User
from access_control.models import Permission, Role, UserAccessEvent, UserAssignment
from organization.models import LegalEntity, Plant, FunctionalArea


class HRApprovalAuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="hr_test_user",
            email="hr_test_user@example.com",
            password="Test-only-password-123!",
        )
        self.token = Token.objects.create(user=self.user)
        self.authenticator = HRApprovedTokenAuthentication()
        self.factory = APIRequestFactory()

    def test_pending_user_token_is_rejected(self):
        request = self.factory.get(
            "/api/auth/me/",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        with self.assertRaises(AuthenticationFailed):
            self.authenticator.authenticate(request)

    def test_approved_user_token_is_accepted(self):
        self.user.hr_approval_status = User.HRApprovalStatus.APPROVED
        self.user.save(update_fields=["hr_approval_status"])
        request = self.factory.get(
            "/api/auth/me/",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        user, returned_token = self.authenticator.authenticate(request)
        self.assertEqual(user.pk, self.user.pk)
        self.assertEqual(returned_token.key, self.token.key)

    def test_revoked_user_token_is_rejected(self):
        self.user.hr_approval_status = User.HRApprovalStatus.REVOKED
        self.user.save(update_fields=["hr_approval_status"])
        request = self.factory.get(
            "/api/auth/me/",
            HTTP_AUTHORIZATION=f"Token {self.token.key}",
        )
        with self.assertRaises(AuthenticationFailed):
            self.authenticator.authenticate(request)


class HRAccessModelTests(TestCase):
    def setUp(self):
        self.actor = User.objects.create_user(
            username="hr_approver_test",
            email="hr_approver_test@example.com",
            password="Test-only-password-123!",
        )
        self.target = User.objects.create_user(
            username="hr_target_test",
            email="hr_target_test@example.com",
            password="Test-only-password-123!",
        )

    def test_grant_hr_access_sets_approval_and_seven_day_deadline(self):
        before = timezone.now()
        self.target.grant_hr_access(self.actor)
        self.target.refresh_from_db()
        self.assertEqual(self.target.hr_approval_status, User.HRApprovalStatus.APPROVED)
        self.assertEqual(self.target.hr_approved_by_id, self.actor.pk)
        self.assertIsNotNone(self.target.access_granted_at)
        self.assertIsNotNone(self.target.employee_master_due_at)
        self.assertGreaterEqual(self.target.access_granted_at, before)
        self.assertEqual(
            self.target.employee_master_due_at - self.target.access_granted_at,
            timedelta(days=7),
        )

    def test_revoke_hr_access_records_actor_and_reason(self):
        reason = "Test-only revocation"
        self.target.revoke_hr_access(self.actor, reason)
        self.target.refresh_from_db()
        self.assertEqual(self.target.hr_approval_status, User.HRApprovalStatus.REVOKED)
        self.assertEqual(self.target.access_revoked_by_id, self.actor.pk)
        self.assertEqual(self.target.access_revocation_reason, reason)
        self.assertIsNotNone(self.target.access_revoked_at)

    def test_access_event_records_actor_and_target(self):
        event = UserAccessEvent.objects.create(
            user=self.target,
            actor=self.actor,
            event_type=UserAccessEvent.EventType.REVOKED,
            reason="Test-only audit event",
        )
        self.assertEqual(event.user_id, self.target.pk)
        self.assertEqual(event.actor_id, self.actor.pk)
        self.assertEqual(event.reason, "Test-only audit event")


class HRAccessEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.entity = LegalEntity.objects.get(code="IEMS-MFG")
        self.plant1 = Plant.objects.get(legal_entity=self.entity, code="PLANT-01")
        self.plant2 = Plant.objects.get(legal_entity=self.entity, code="PLANT-02")
        self.hr_area = FunctionalArea.objects.get(code="CORPORATE_GOVERNANCE")
        self.approve_permission = Permission.objects.get(code="employees.hr_operations.approve")
        self.central_role = Role.objects.get(code="CENTRAL_HR")
        self.manager_role = Role.objects.get(code="PLANT_HR_MANAGER")
        self.executive_role = Role.objects.get(code="PLANT_HR_EXECUTIVE")
        self.employee_master_role = Role.objects.get(code="HR_EMPLOYEE_MASTER_MANAGER")

        self.central_hr = self.make_user("central_hr")
        self.plant_manager = self.make_user("plant_manager")
        self.plant_executive = self.make_user("plant_executive")
        self.employee_master_manager = self.make_user("employee_master")
        self.target = self.make_user("target_user")

        self.assign(self.central_hr, self.central_role, None)
        self.assign(self.plant_manager, self.manager_role, self.plant1)
        self.assign(self.plant_executive, self.executive_role, self.plant1)
        self.assign(self.employee_master_manager, self.employee_master_role, None)
        self.assign(self.target, self.manager_role, self.plant1)

        self.central_hr.grant_hr_access(self.central_hr)
        self.plant_manager.grant_hr_access(self.plant_manager)
        self.plant_executive.grant_hr_access(self.plant_executive)
        self.employee_master_manager.grant_hr_access(self.employee_master_manager)

    def make_user(self, prefix):
        return User.objects.create_user(
            username=prefix,
            email=f"{prefix}@example.com",
            password="Test-only-password-123!",
        )

    def assign(self, user, role, plant):
        UserAssignment.objects.create(
            user=user,
            role=role,
            legal_entity=self.entity,
            plant=plant,
            is_active=True,
            is_primary=True,
        )

    def authenticate_as(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return token

    def post_action(self, actor, target, action, **extra):
        self.authenticate_as(actor)
        data = {"legal_entity_id": self.entity.pk, **extra}
        if actor == self.plant_manager:
            data["plant_id"] = self.plant1.pk
        return self.client.post(f"/api/auth/access/{target.pk}/{action}/", data, format="json")

    def test_central_hr_can_approve_user(self):
        response = self.post_action(self.central_hr, self.target, "approve")
        self.assertEqual(response.status_code, 200, response.data)
        self.target.refresh_from_db()
        self.assertEqual(self.target.hr_approval_status, User.HRApprovalStatus.APPROVED)
        self.assertTrue(UserAccessEvent.objects.filter(
            user=self.target, actor=self.central_hr,
            event_type=UserAccessEvent.EventType.APPROVED,
        ).exists())

    def test_plant_manager_cannot_manage_user_with_other_plant_assignment(self):
        self.assign(self.target, self.manager_role, self.plant2)
        response = self.post_action(self.plant_manager, self.target, "approve")
        self.assertEqual(response.status_code, 403)

    def test_plant_executive_cannot_approve(self):
        response = self.post_action(self.plant_executive, self.target, "approve")
        self.assertEqual(response.status_code, 403)

    def test_employee_master_manager_cannot_approve(self):
        response = self.post_action(self.employee_master_manager, self.target, "approve")
        self.assertEqual(response.status_code, 403)

    def test_rejection_requires_reason(self):
        response = self.post_action(self.central_hr, self.target, "reject")
        self.assertEqual(response.status_code, 400)

    def test_rejection_deletes_token_and_records_audit_event(self):
        target_token, _ = Token.objects.get_or_create(user=self.target)
        response = self.post_action(
            self.central_hr, self.target, "reject", reason="Test rejection"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(Token.objects.filter(pk=target_token.pk).exists())
        self.assertTrue(UserAccessEvent.objects.filter(
            user=self.target, actor=self.central_hr,
            event_type=UserAccessEvent.EventType.REJECTED,
            reason="Test rejection",
        ).exists())

    def test_self_approval_is_rejected(self):
        response = self.post_action(self.central_hr, self.central_hr, "approve")
        self.assertEqual(response.status_code, 400)

    def test_revocation_deletes_token_and_records_audit_event(self):
        self.target.grant_hr_access(self.central_hr)
        target_token, _ = Token.objects.get_or_create(user=self.target)
        response = self.post_action(
            self.central_hr, self.target, "revoke", reason="Test revocation"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(Token.objects.filter(pk=target_token.pk).exists())
        self.target.refresh_from_db()
        self.assertEqual(self.target.hr_approval_status, User.HRApprovalStatus.REVOKED)
        self.assertTrue(UserAccessEvent.objects.filter(
            user=self.target, actor=self.central_hr,
            event_type=UserAccessEvent.EventType.REVOKED,
            reason="Test revocation",
        ).exists())

    def test_plant_manager_can_approve_user_in_assigned_plant(self):
        response = self.post_action(self.plant_manager, self.target, "approve")
        self.assertEqual(response.status_code, 200, response.data)
        self.target.refresh_from_db()
        self.assertEqual(self.target.hr_approval_status, User.HRApprovalStatus.APPROVED)

    def test_rejected_users_existing_token_cannot_authenticate(self):
        target_token, _ = Token.objects.get_or_create(user=self.target)
        response = self.post_action(
            self.central_hr, self.target, "reject", reason="Test rejection"
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertFalse(Token.objects.filter(pk=target_token.pk).exists())
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {target_token.key}")
        auth_response = self.client.get("/api/auth/me/")
        self.assertEqual(auth_response.status_code, 401)

    def test_central_hr_cannot_manage_access_in_another_legal_entity_scope(self):
        self.authenticate_as(self.central_hr)
        other_entity_id = self.entity.pk + 999999

        response = self.client.post(
            f"/api/auth/access/{self.target.pk}/approve/",
            {
                "legal_entity_id": other_entity_id,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403, response.data)
        self.target.refresh_from_db()
        self.assertEqual(
            self.target.hr_approval_status,
            User.HRApprovalStatus.PENDING,
        )

    def test_plant_manager_cannot_submit_unauthorized_plant_id(self):
        self.authenticate_as(self.plant_manager)
        response = self.client.post(
            f"/api/auth/access/{self.target.pk}/approve/",
            {
                "legal_entity_id": self.entity.pk,
                "plant_id": self.plant2.pk,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403, response.data)
        self.target.refresh_from_db()
        self.assertEqual(
            self.target.hr_approval_status,
            User.HRApprovalStatus.PENDING,
        )
