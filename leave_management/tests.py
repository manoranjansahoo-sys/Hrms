from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from employees.models import EmployeeProfile
from organization.models import Department, Designation, Site
from leave_management.models import LeaveType, LeaveBalance, LeaveRequest
from decimal import Decimal
from datetime import date, timedelta


class LeaveManagementQueueTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Users
        self.hr_user = CustomUser.objects.create_user(
            username='hr_test', email='hr@test.com', password='password123',
            role=CustomUser.Role.HR, first_name='HR', last_name='Tester'
        )
        self.emp_user = CustomUser.objects.create_user(
            username='emp_test', email='emp@test.com', password='password123',
            role=CustomUser.Role.EMPLOYEE, first_name='Employee', last_name='Tester'
        )

        # Org
        self.site = Site.objects.create(name='Bhubaneswar Campus', code='BBSR', city='Bhubaneswar')
        self.dept = Department.objects.create(name='Engineering', code='ENG')
        self.desig = Designation.objects.create(title='Software Engineer', department=self.dept)

        self.employee = EmployeeProfile.objects.create(
            user=self.emp_user,
            emp_id='EMP999',
            site=self.site,
            department=self.dept,
            designation=self.desig,
            joining_date=date(2025, 1, 1),
            employment_type='FULL_TIME'
        )

        self.leave_type_pl, _ = LeaveType.objects.get_or_create(
            code='PL',
            defaults={
                'name': 'Paid Leave',
                'days_per_year': Decimal('18.0'),
                'is_paid': True
            }
        )
        self.leave_type_sl, _ = LeaveType.objects.get_or_create(
            code='SL',
            defaults={
                'name': 'Sick Leave',
                'days_per_year': Decimal('12.0'),
                'is_paid': True
            }
        )

        self.balance_pl, _ = LeaveBalance.objects.get_or_create(
            employee=self.employee,
            leave_type=self.leave_type_pl,
            year=2026,
            defaults={'allocated_days': Decimal('18.0'), 'used_days': Decimal('2.0'), 'pending_days': Decimal('2.0')}
        )
        self.balance_pl.allocated_days = Decimal('18.0')
        self.balance_pl.used_days = Decimal('2.0')
        self.balance_pl.pending_days = Decimal('2.0')
        self.balance_pl.save()

        self.balance_sl, _ = LeaveBalance.objects.get_or_create(
            employee=self.employee,
            leave_type=self.leave_type_sl,
            year=2026,
            defaults={'allocated_days': Decimal('12.0'), 'used_days': Decimal('1.0'), 'pending_days': Decimal('0.0')}
        )
        self.balance_sl.allocated_days = Decimal('12.0')
        self.balance_sl.used_days = Decimal('1.0')
        self.balance_sl.pending_days = Decimal('0.0')
        self.balance_sl.save()

        self.leave_req = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type_pl,
            start_date=date(2026, 11, 10),
            end_date=date(2026, 11, 11),
            total_days=Decimal('2.0'),
            reason='Family celebration and personal commitments',
            status=LeaveRequest.Status.PENDING_MANAGER
        )

    def test_queue_access_requires_auth(self):
        url = reverse('leave_management:admin_queue')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_queue_renders_for_hr(self):
        self.client.force_login(self.hr_user)
        url = reverse('leave_management:admin_queue')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Leave Approvals & Workflow Queue')
        self.assertContains(response, 'Employee Tester')
        self.assertContains(response, 'EMP999')
        self.assertEqual(response.context['count_all'], 1)
        self.assertEqual(response.context['count_pending_mgr'], 1)

    def test_hr_final_approve_leave(self):
        self.client.force_login(self.hr_user)
        url = reverse('leave_management:process_leave', kwargs={'request_id': self.leave_req.id})
        response = self.client.post(url, {'action': 'APPROVE', 'remarks': 'Approved by HR'})
        self.assertRedirects(response, reverse('leave_management:admin_queue'))

        self.leave_req.refresh_from_db()
        self.assertEqual(self.leave_req.status, LeaveRequest.Status.APPROVED)
        self.assertEqual(self.leave_req.hr_decision, 'APPROVED')
        self.assertEqual(self.leave_req.hr_remarks, 'Approved by HR')

    def test_reject_leave_with_remarks(self):
        self.client.force_login(self.hr_user)
        url = reverse('leave_management:process_leave', kwargs={'request_id': self.leave_req.id})
        response = self.client.post(url, {'action': 'REJECT', 'remarks': 'Insufficient notice period'})
        self.assertRedirects(response, reverse('leave_management:admin_queue'))

        self.leave_req.refresh_from_db()
        self.assertEqual(self.leave_req.status, LeaveRequest.Status.REJECTED)
        self.assertEqual(self.leave_req.hr_decision, 'REJECTED')
        self.assertEqual(self.leave_req.hr_remarks, 'Insufficient notice period')

    def test_queue_shows_employee_sick_leave_paid_leave_balances_and_reason(self):
        self.client.force_login(self.hr_user)
        url = reverse('leave_management:admin_queue')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 1. Checks that reason is displayed
        self.assertContains(response, 'Family celebration and personal commitments')

        # 2. Checks that Sick Leave & Paid Leave balances are shown in the modal
        self.assertContains(response, 'Sick Leave (SL)')
        self.assertContains(response, 'Paid Leave (PL)')
        self.assertContains(response, '11.0 Days Left') # SL: 12 allocated - 1 used - 0 pending = 11 available
        self.assertContains(response, '14.0 Days Left') # PL: 18 allocated - 2 used - 2 pending = 14 available
        
        # 3. Checks that table row is clean without SL/PL clutter badges
        self.assertNotContains(response, 'SL: <b>')
        self.assertNotContains(response, 'PL: <b>')

    def test_two_leave_types_configuration(self):
        # Company only has Sick Leave and Paid Leave
        codes = list(LeaveType.objects.values_list('code', flat=True))
        self.assertIn('SL', codes)
        self.assertIn('PL', codes)

    def test_approve_and_reject_buttons_always_visible_in_modal_for_approved_requests(self):
        # Mark request as already approved
        self.leave_req.status = LeaveRequest.Status.APPROVED
        self.leave_req.hr_decision = 'APPROVED'
        self.leave_req.save()

        self.client.force_login(self.hr_user)
        response = self.client.get(reverse('leave_management:admin_queue'))
        self.assertEqual(response.status_code, 200)

        # Both Approve and Reject buttons must always be present in the modal
        self.assertContains(response, 'value="APPROVE"')
        self.assertContains(response, 'value="REJECT"')
        self.assertContains(response, 'Currently Approved')

    def test_hr_can_modify_approved_leave_to_rejected_and_reverts_balance(self):
        # First approve the leave
        self.client.force_login(self.hr_user)
        url = reverse('leave_management:process_leave', kwargs={'request_id': self.leave_req.id})
        self.client.post(url, {'action': 'APPROVE', 'remarks': 'Initial approval'})

        self.leave_req.refresh_from_db()
        self.balance_pl.refresh_from_db()
        self.assertEqual(self.leave_req.status, LeaveRequest.Status.APPROVED)
        used_after_approve = self.balance_pl.used_days

        # HR modifies it to REJECT because it was wrongly approved
        self.client.post(url, {'action': 'REJECT', 'remarks': 'Wrongly approved by HR, modifying to rejected'})

        self.leave_req.refresh_from_db()
        self.balance_pl.refresh_from_db()
        self.assertEqual(self.leave_req.status, LeaveRequest.Status.REJECTED)
        self.assertEqual(self.leave_req.hr_decision, 'REJECTED')
        self.assertEqual(self.leave_req.hr_remarks, 'Wrongly approved by HR, modifying to rejected')
        # Balance used_days must be reverted back
        self.assertEqual(self.balance_pl.used_days, used_after_approve - self.leave_req.total_days)

    def test_apply_leave_page_renders_clean_light_cards(self):
        self.client.force_login(self.emp_user)
        response = self.client.get(reverse('leave_management:apply_leave'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Paid Leave Available')
        self.assertContains(response, 'Sick Leave Available')
        self.assertContains(response, 'Allocated:')
        self.assertContains(response, 'halfDayCheck')

    def test_apply_half_day_leave_with_single_date(self):
        self.client.force_login(self.emp_user)
        # Omit end_date because half-day uses single date
        post_data = {
            'leave_type': self.leave_type_pl.id,
            'is_half_day': 'on',
            'start_date': '2026-11-25',
            'reason': 'Personal appointment in first half',
        }
        response = self.client.post(reverse('leave_management:apply_leave'), post_data)
        self.assertRedirects(response, reverse('leave_management:my_leaves'))

        created = LeaveRequest.objects.filter(employee=self.employee, start_date='2026-11-25').first()
        self.assertIsNotNone(created)
        self.assertTrue(created.is_half_day)
        self.assertEqual(created.end_date, date(2026, 11, 25))
        self.assertEqual(created.total_days, Decimal('0.5'))

    def test_queue_duration_column_half_day_only(self):
        # Create a half day leave request
        half_day_req = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type_pl,
            start_date=date(2026, 11, 28),
            end_date=date(2026, 11, 28),
            is_half_day=True,
            total_days=Decimal('0.5'),
            reason='Half day doctor visit',
            status=LeaveRequest.Status.PENDING_MANAGER
        )
        self.client.force_login(self.hr_user)
        response = self.client.get(reverse('leave_management:admin_queue'))
        self.assertEqual(response.status_code, 200)

        # In Duration column, Half Day is rendered directly inside lq-days-pill
        self.assertContains(response, '<span>Half Day</span>')
        self.assertNotContains(response, '0.5 Days')
        self.assertNotContains(response, '0.5 Day')
