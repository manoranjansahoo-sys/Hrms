from django.test import TestCase, Client
from django.utils import timezone
from decimal import Decimal
import datetime
from accounts.models import CustomUser
from employees.models import EmployeeProfile
from organization.models import Department, Designation, Site, Holiday, OperatingSchedule
from attendance.models import Attendance, Shift
from leave_management.models import LeaveRequest
from payroll.models import PayrollPeriod, Payslip, SalaryStructure
from payroll.calculator import compute_employee_salary, get_office_hours_and_grace, round_decimal


class UnifiedMasterFormulaTests(TestCase):
    """
    Unit and integration tests for the Unified Master Salary Calculation Formula.
    """

    def setUp(self):
        # Department, Designation, Site
        self.dept, _ = Department.objects.get_or_create(code='ENG', defaults={'name': 'Engineering'})
        self.desig, _ = Designation.objects.get_or_create(title='Software Engineer', department=self.dept)
        self.site, _ = Site.objects.get_or_create(code='HQ', defaults={'name': 'HQ Tech Park', 'address': 'Bengaluru'})

        # Create user & employee profile
        self.user, _ = CustomUser.objects.get_or_create(
            username='test_dev',
            defaults={
                'email': 'test_dev@example.com',
                'first_name': 'Aarav',
                'last_name': 'Sharma',
                'role': CustomUser.Role.EMPLOYEE
            }
        )
        self.user.set_password('Password@123')
        self.user.save()

        self.hr_user, _ = CustomUser.objects.get_or_create(
            username='test_hr',
            defaults={
                'email': 'test_hr@example.com',
                'first_name': 'Priya',
                'last_name': 'Patel',
                'role': CustomUser.Role.HR
            }
        )
        self.hr_user.set_password('Password@123')
        self.hr_user.save()

        self.employee, _ = EmployeeProfile.objects.get_or_create(
            emp_id='EMP999',
            defaults={
                'user': self.user,
                'joining_date': datetime.date(2025, 1, 1),
                'department': self.dept,
                'designation': self.desig,
                'site': self.site,
                'status': 'ACTIVE'
            }
        )

        # Salary Structure: Basic 60,000
        self.salary_struct, _ = SalaryStructure.objects.update_or_create(
            employee=self.employee,
            defaults={
                'basic_salary': Decimal('60000.00'),
                'hra': Decimal('24000.00'),
                'conveyance_allowance': Decimal('3000.00'),
                'medical_allowance': Decimal('2000.00'),
                'special_allowance': Decimal('5000.00'),
                'provident_fund': Decimal('1800.00'),
                'professional_tax': Decimal('200.00'),
                'tds': Decimal('1000.00')
            }
        )

        # Standard Shift: 09:30 to 18:30 (9.0 hours)
        self.shift, _ = Shift.objects.get_or_create(
            name='Standard Shift',
            defaults={
                'start_time': datetime.time(9, 30),
                'end_time': datetime.time(18, 30),
                'grace_period_minutes': 15,
                'is_default': True
            }
        )

        # 2026 October Holidays: 19th & 20th Dussehra
        Holiday.objects.get_or_create(
            date=datetime.date(2026, 10, 19),
            defaults={'title': 'Dussehra Day 1', 'is_optional': False}
        )
        Holiday.objects.get_or_create(
            date=datetime.date(2026, 10, 20),
            defaults={'title': 'Dussehra Day 2', 'is_optional': False}
        )

    def test_base_rates_calculation(self):
        """
        Base Rates:
        Per-Day Rate = Monthly Base Salary / 30 = 60,000 / 30 = 2,000.00
        Required Daily Hours = 18:30 - 09:30 = 9.0 hrs
        Per-Minute Rate = 2,000 / (9.0 * 60) = 3.7037
        """
        calc = compute_employee_salary(self.employee, year=2026, month=10, allow_overtime_compensation=True)
        self.assertEqual(calc['monthly_base_salary'], Decimal('60000.00'))
        self.assertEqual(calc['per_day_rate'], Decimal('2000.00'))
        self.assertEqual(calc['required_daily_hours'], Decimal('9.0'))
        self.assertEqual(calc['per_minute_rate'], Decimal('3.7037'))

    def test_part_a_holiday_and_sunday_exclusion(self):
        """
        In October 2026:
        Total Calendar Days = 31
        Sundays (4, 11, 18, 25) = 4 weekly offs
        Public Holidays (19, 20) = 2 public holidays
        Working Days = 31 - 4 - 2 = 25 working days.
        """
        calc = compute_employee_salary(self.employee, year=2026, month=10, allow_overtime_compensation=True)
        self.assertEqual(calc['calendar_days_in_month'], 31)
        self.assertEqual(calc['weekly_offs_count'], 4)
        self.assertEqual(calc['public_holidays_count'], 2)
        self.assertEqual(calc['working_days_count'], 25)

    def test_part_b_late_and_overtime_shortfall_with_compensation(self):
        """
        Test Late Arrival and Overtime compensation:
        Day 1 (Oct 1, 2026):
          Check-in: 10:00 (30 mins late from 09:30, beyond 15 min grace => 30 late mins)
          Check-out: 19:15 (45 mins OT past 18:30)
          With OT compensation: Net Shortfall = max(0, 30 - 45) = 0 mins. Auto-waived!
        Day 2 (Oct 2, 2026):
          Check-in: 10:15 (45 mins late)
          Check-out: 18:30 (0 mins OT)
          Net Shortfall = 45 mins.
          Deduction = 45 * 3.7037 = 166.67
        """
        Attendance.objects.filter(employee=self.employee).delete()
        Attendance.objects.create(
            employee=self.employee,
            date=datetime.date(2026, 10, 1),
            punch_in=datetime.datetime(2026, 10, 1, 10, 0),
            punch_out=datetime.datetime(2026, 10, 1, 19, 15),
            status='PRESENT',
            is_late=True
        )
        Attendance.objects.create(
            employee=self.employee,
            date=datetime.date(2026, 10, 2),
            punch_in=datetime.datetime(2026, 10, 2, 10, 15),
            punch_out=datetime.datetime(2026, 10, 2, 18, 30),
            status='PRESENT',
            is_late=True
        )

        calc = compute_employee_salary(self.employee, year=2026, month=10, allow_overtime_compensation=True)
        self.assertEqual(calc['total_late_minutes'], 75)
        self.assertEqual(calc['total_overtime_minutes'], 45)
        self.assertEqual(calc['net_shortfall_minutes'], 45)  # Day 1 offset by OT, Day 2 has 45 mins shortfall
        self.assertEqual(calc['shortfall_deduction'], Decimal('166.67'))

    def test_part_c_gross_deduction_and_hr_condone(self):
        """
        Gross Deduction = Leave Deduction + Shortfall Deduction
        HR Condonation:
        Final Deduction = max(0, Gross Deduction - HR Condone)
        Net Payable = max(0, Base Salary - Final Deduction)
        """
        Attendance.objects.filter(employee=self.employee).delete()
        # Create full attendance for all 25 working days so unexcused = 0
        for d in range(1, 32):
            dt = datetime.date(2026, 10, d)
            if dt.weekday() == 6 or dt in [datetime.date(2026, 10, 19), datetime.date(2026, 10, 20)]:
                continue
            # Late on day 1 with 45 mins net shortfall
            cin = datetime.datetime(2026, 10, d, 10, 15) if d == 1 else datetime.datetime(2026, 10, d, 9, 30)
            cout = datetime.datetime(2026, 10, d, 18, 30)
            Attendance.objects.create(
                employee=self.employee,
                date=dt,
                punch_in=cin,
                punch_out=cout,
                status='PRESENT'
            )

        calc = compute_employee_salary(self.employee, year=2026, month=10, allow_overtime_compensation=True)
        self.assertEqual(calc['unexcused_absences'], Decimal('0.0'))
        self.assertEqual(calc['leave_deduction'], Decimal('0.00'))
        self.assertEqual(calc['net_shortfall_minutes'], 45)
        self.assertEqual(calc['shortfall_deduction'], Decimal('166.67'))
        self.assertEqual(calc['gross_deduction'], Decimal('166.67'))

        # Base 60,000 - 166.67 = 59,833.33
        self.assertEqual(calc['net_payable'], Decimal('59833.33'))

    def test_hr_condone_view_action(self):
        """
        Test HR condone view updating the payslip with waiver and recalculating Net.
        """
        period = PayrollPeriod.objects.create(
            month=10,
            year=2026,
            working_days=25,
            status='SUBMITTED',
            processed_by=self.hr_user
        )

        payslip = Payslip.objects.create(
            employee=self.employee,
            payroll_period=period,
            month=10,
            year=2026,
            basic_salary=Decimal('60000.00'),
            gross_deduction=Decimal('2000.00'),
            hr_condoned_amount=Decimal('0.00'),
            final_deduction=Decimal('2000.00'),
            net_payable=Decimal('58000.00'),
            total_deductions=Decimal('2000.00')
        )

        client = Client(SERVER_NAME='localhost', HTTP_HOST='localhost')
        client.force_login(self.hr_user)

        response = client.post(f'/payroll/payslips/{payslip.id}/condone/', {
            'condoned_amount': '1500.00',
            'reason': 'Approved emergency waiver'
        })
        self.assertEqual(response.status_code, 302)

        payslip.refresh_from_db()
        self.assertEqual(payslip.hr_condoned_amount, Decimal('1500.00'))
        self.assertEqual(payslip.final_deduction, Decimal('500.00'))
        self.assertEqual(payslip.net_payable, Decimal('59500.00'))
        self.assertEqual(payslip.condone_reason, 'Approved emergency waiver')

    def test_payslip_pdf_generation(self):
        """
        Verify PDF generation generates a valid PDF stream and HTTP view returns 200.
        """
        from payroll.pdf_generator import generate_payslip_pdf

        period = PayrollPeriod.objects.create(
            month=10,
            year=2026,
            working_days=25,
            status='APPROVED',
            processed_by=self.hr_user
        )

        payslip = Payslip.objects.create(
            employee=self.employee,
            payroll_period=period,
            month=10,
            year=2026,
            basic_salary=Decimal('60000.00'),
            gross_deduction=Decimal('2000.00'),
            hr_condoned_amount=Decimal('500.00'),
            final_deduction=Decimal('1500.00'),
            net_payable=Decimal('58500.00'),
            total_deductions=Decimal('1500.00')
        )

        pdf_buf = generate_payslip_pdf(payslip)
        self.assertGreater(len(pdf_buf.getvalue()), 1000)

        client = Client(SERVER_NAME='localhost', HTTP_HOST='localhost')
        client.force_login(self.hr_user)
        response = client.get(f'/payroll/payslips/{payslip.id}/pdf/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', response['Content-Disposition'])

    def test_payroll_period_reports_export(self):
        """
        Verify Monthly Payroll Report download by Admin / HR in CSV, Excel (.xlsx), and PDF formats.
        """
        period = PayrollPeriod.objects.create(
            month=10,
            year=2026,
            working_days=25,
            status='SUBMITTED',
            processed_by=self.hr_user,
            office_start_time=datetime.time(9, 30),
            office_end_time=datetime.time(18, 30),
            required_daily_hours=9.0,
            allow_overtime_compensation=True
        )

        payslip = Payslip.objects.create(
            employee=self.employee,
            payroll_period=period,
            month=10,
            year=2026,
            basic_salary=Decimal('60000.00'),
            per_day_rate=Decimal('2000.00'),
            per_minute_rate=Decimal('3.70'),
            total_working_days=Decimal('25.0'),
            payable_days=Decimal('23.0'),
            excess_sl=Decimal('1.0'),
            excess_cl=Decimal('0.0'),
            unexcused_absences=1,
            leave_deduction=Decimal('4000.00'),
            total_late_minutes=60,
            total_overtime_minutes=45,
            net_shortfall_minutes=15,
            shortfall_deduction=Decimal('55.50'),
            gross_deduction=Decimal('4055.50'),
            hr_condoned_amount=Decimal('55.50'),
            final_deduction=Decimal('4000.00'),
            net_payable=Decimal('56000.00'),
            total_deductions=Decimal('7000.00'),
            status='GENERATED'
        )

        client = Client(SERVER_NAME='localhost', HTTP_HOST='localhost')

        # 1. Unauthorized / non-HR employee should be blocked
        client.force_login(self.user)
        resp_unauth = client.get(f'/payroll/period/{period.id}/export/csv/')
        self.assertIn(resp_unauth.status_code, [302, 403])

        # 2. HR can download CSV
        client.force_login(self.hr_user)
        resp_csv = client.get(f'/payroll/period/{period.id}/export/csv/')
        self.assertEqual(resp_csv.status_code, 200)
        self.assertIn('text/csv', resp_csv['Content-Type'])
        self.assertIn('Payroll_Report_October_2026.csv', resp_csv['Content-Disposition'])
        csv_content = resp_csv.content.decode('utf-8')
        self.assertIn('Aarav Sharma', csv_content)
        self.assertIn('EMP999', csv_content)
        self.assertIn('COMPANY HRMS ENTERPRISE', csv_content)

        # 3. HR can download Excel (.xlsx)
        resp_excel = client.get(f'/payroll/period/{period.id}/export/excel/')
        self.assertEqual(resp_excel.status_code, 200)
        self.assertEqual(resp_excel['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('Payroll_Report_October_2026.xlsx', resp_excel['Content-Disposition'])
        self.assertGreater(len(resp_excel.content), 2000)

        # 4. HR can download PDF (.pdf)
        resp_pdf = client.get(f'/payroll/period/{period.id}/export/pdf/')
        self.assertEqual(resp_pdf.status_code, 200)
        self.assertEqual(resp_pdf['Content-Type'], 'application/pdf')
        self.assertIn('Payroll_Report_October_2026.pdf', resp_pdf['Content-Disposition'])
        self.assertTrue(resp_pdf.content.startswith(b'%PDF'))

