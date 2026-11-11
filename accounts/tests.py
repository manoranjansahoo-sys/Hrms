from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal
from accounts.models import CustomUser
from organization.models import Department, Designation, Site
from employees.models import EmployeeProfile
from attendance.models import Attendance, Shift
from leave_management.models import LeaveType, LeaveBalance, LeaveRequest
from payroll.models import PayrollPeriod, Payslip, SalaryStructure
from payroll.pdf_generator import generate_payslip_pdf


class HRMSEnterpriseTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create Department, Designation, Site
        self.dept = Department.objects.create(name='Technology', code='TECH')
        self.desig = Designation.objects.create(title='Engineer', department=self.dept)
        self.site = Site.objects.create(name='Bengaluru HQ', code='BLR', city='Bengaluru')

        # Create 4 Authority Users
        # 1. Employee
        self.emp_user = CustomUser.objects.create_user(
            username='emp_test', password='password123',
            role=CustomUser.Role.EMPLOYEE, first_name='John', last_name='Tester'
        )
        self.emp_profile = EmployeeProfile.objects.create(
            user=self.emp_user, emp_id='EMP991', department=self.dept,
            designation=self.desig, site=self.site,
            employment_type=EmployeeProfile.EmploymentType.FULL_TIME,
            joining_date=date(2023, 1, 1),
            bank_name='Test Bank', bank_account_number='9876543210'
        )

        # 2. Site Manager
        self.mgr_user = CustomUser.objects.create_user(
            username='mgr_test', password='password123',
            role=CustomUser.Role.SITE_MANAGER, first_name='Manager', last_name='Tester'
        )
        self.site.site_manager = self.mgr_user
        self.site.save()

        # 3. HR Admin
        self.hr_user = CustomUser.objects.create_user(
            username='hr_test', password='password123',
            role=CustomUser.Role.HR, first_name='HR', last_name='Tester'
        )

        # 4. Head of Company
        self.head_user = CustomUser.objects.create_user(
            username='head_test', password='password123',
            role=CustomUser.Role.HEAD, first_name='Head', last_name='Tester'
        )

        # Shifts
        self.shift = Shift.objects.create(
            name='General Shift',
            start_time=timezone.datetime.strptime('09:00', '%H:%M').time(),
            end_time=timezone.datetime.strptime('18:00', '%H:%M').time(),
            is_default=True
        )

        # Leave Types & Balances
        self.lt_pl, _ = LeaveType.objects.get_or_create(
            code='PL',
            defaults={'name': 'Paid Leave', 'days_per_year': Decimal('18.0'), 'is_paid': True}
        )
        self.bal, _ = LeaveBalance.objects.get_or_create(
            employee=self.emp_profile, leave_type=self.lt_pl, year=2026,
            defaults={'allocated_days': Decimal('18.0'), 'used_days': Decimal('0.0'), 'pending_days': Decimal('0.0')}
        )

        # Salary Structure
        self.salary_struct = SalaryStructure.objects.create(
            employee=self.emp_profile,
            basic_salary=Decimal('50000.00'),
            hra=Decimal('25000.00'),
            conveyance_allowance=Decimal('5000.00'),
            medical_allowance=Decimal('5000.00'),
            special_allowance=Decimal('15000.00'),
            provident_fund=Decimal('6000.00'),
            professional_tax=Decimal('200.00'),
            tds=Decimal('4000.00')
        )

    # 1. RBAC Tests: Backend Permissions
    def test_employee_cannot_access_hr_dashboard(self):
        """Strict RBAC: Regular employee must receive HTTP 403 Forbidden on HR Dashboard."""
        self.client.login(username='emp_test', password='password123')
        response = self.client.get(reverse('portal:dashboard_hr'))
        self.assertEqual(response.status_code, 403)

    def test_employee_cannot_access_head_dashboard(self):
        """Strict RBAC: Regular employee must receive HTTP 403 Forbidden on Head Dashboard."""
        self.client.login(username='emp_test', password='password123')
        response = self.client.get(reverse('portal:dashboard_head'))
        self.assertEqual(response.status_code, 403)

    def test_hr_can_access_hr_dashboard(self):
        """HR Administrator successfully accesses HR Dashboard."""
        self.client.login(username='hr_test', password='password123')
        response = self.client.get(reverse('portal:dashboard_hr'))
        self.assertEqual(response.status_code, 200)

    def test_site_manager_can_access_site_dashboard(self):
        """Site Manager successfully accesses Site Manager Dashboard."""
        self.client.login(username='mgr_test', password='password123')
        response = self.client.get(reverse('portal:dashboard_site_manager'))
        self.assertEqual(response.status_code, 200)

    def test_head_can_access_head_dashboard(self):
        """Head of Company successfully accesses Executive Head Dashboard."""
        self.client.login(username='head_test', password='password123')
        response = self.client.get(reverse('portal:dashboard_head'))
        self.assertEqual(response.status_code, 200)

    # 2. Attendance Workflow: Punch In / Punch Out
    def test_punch_in_and_punch_out_workflow(self):
        """Test Punch In, record timestamp, then Punch Out and compute working hours."""
        self.client.login(username='emp_test', password='password123')

        # Punch In
        response = self.client.get(reverse('attendance:punch_in'))
        self.assertEqual(response.status_code, 302)

        today = timezone.localdate()
        att = Attendance.objects.get(employee=self.emp_profile, date=today)
        self.assertIsNotNone(att.punch_in)
        self.assertEqual(att.status, 'PRESENT')

        # Simulate punch out 8.5 hours later
        att.punch_out = att.punch_in + timedelta(hours=8, minutes=30)
        att.calculate_hours()
        att.save()

        self.assertEqual(att.working_hours, Decimal('8.50'))
        self.assertEqual(att.overtime_hours, Decimal('0.50'))
        self.assertEqual(att.status, 'PRESENT')

    # 3. Leave Management Workflow: Apply, Recommend, Approve
    def test_leave_application_and_approval_workflow(self):
        """Test complete leave workflow from submission to multi-tier approval."""
        self.client.login(username='emp_test', password='password123')
        today = timezone.localdate()

        # Submit leave application
        response = self.client.post(reverse('leave_management:apply_leave'), {
            'leave_type': self.lt_pl.id,
            'start_date': (today + timedelta(days=2)).strftime('%Y-%m-%d'),
            'end_date': (today + timedelta(days=3)).strftime('%Y-%m-%d'),
            'reason': 'Family vacation trip',
        })
        self.assertEqual(response.status_code, 302)

        leave_req = LeaveRequest.objects.filter(employee=self.emp_profile).first()
        self.assertIsNotNone(leave_req)
        self.assertEqual(leave_req.status, LeaveRequest.Status.PENDING_MANAGER)

        # Site Manager Recommends Leave
        self.client.login(username='mgr_test', password='password123')
        response = self.client.post(reverse('leave_management:process_leave', kwargs={'request_id': leave_req.id}), {
            'action': 'RECOMMEND',
            'remarks': 'Coverage confirmed. Recommended.'
        })
        self.assertEqual(response.status_code, 302)
        leave_req.refresh_from_db()
        self.assertEqual(leave_req.status, LeaveRequest.Status.PENDING_HR)

        # HR Final Approves Leave
        self.client.login(username='hr_test', password='password123')
        response = self.client.post(reverse('leave_management:process_leave', kwargs={'request_id': leave_req.id}), {
            'action': 'APPROVE',
            'remarks': 'Leave approved.'
        })
        self.assertEqual(response.status_code, 302)
        leave_req.refresh_from_db()
        self.assertEqual(leave_req.status, LeaveRequest.Status.APPROVED)

        # Check balance was deducted
        self.bal.refresh_from_db()
        self.assertEqual(self.bal.used_days, leave_req.total_days)

    # 4. Payroll & PDF Payslip Generation and Confidentiality
    def test_payroll_and_payslip_generation(self):
        """Test payroll computation, payslip creation, and PDF generator."""
        period = PayrollPeriod.objects.create(
            month=10, year=2026, working_days=26, status='DRAFT', processed_by=self.hr_user
        )

        payslip = Payslip.objects.create(
            payroll_period=period,
            employee=self.emp_profile,
            month=10, year=2026,
            total_working_days=Decimal('26.0'),
            present_days=Decimal('26.0'),
            payable_days=Decimal('26.0'),
            basic_salary=Decimal('50000.00'),
            hra=Decimal('25000.00'),
            conveyance_allowance=Decimal('5000.00'),
            medical_allowance=Decimal('5000.00'),
            special_allowance=Decimal('15000.00'),
            gross_earnings=Decimal('100000.00'),
            provident_fund=Decimal('6000.00'),
            professional_tax=Decimal('200.00'),
            tds=Decimal('4000.00'),
            total_deductions=Decimal('10200.00'),
            net_payable=Decimal('89800.00'),
            status='APPROVED'
        )

        # Generate ReportLab PDF
        pdf_buffer = generate_payslip_pdf(payslip)
        pdf_bytes = pdf_buffer.getvalue()
        self.assertTrue(len(pdf_bytes) > 1000) # PDF contains valid binary data
        self.assertTrue(pdf_bytes.startswith(b'%PDF')) # Valid PDF signature

        # Security check: Employee can download their own payslip
        self.client.login(username='emp_test', password='password123')
        response = self.client.get(reverse('payroll:download_pdf', kwargs={'payslip_id': payslip.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

        # Another employee cannot download this payslip
        other_user = CustomUser.objects.create_user(username='other_emp', password='password123', role=CustomUser.Role.EMPLOYEE)
        self.client.login(username='other_emp', password='password123')
        response = self.client.get(reverse('payroll:download_pdf', kwargs={'payslip_id': payslip.id}))
        self.assertEqual(response.status_code, 403)
