from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, datetime
from accounts.models import CustomUser
from employees.models import EmployeeProfile
from organization.models import Department, Designation, Site
from attendance.models import AttendanceCorrectionRequest, Attendance, Shift


class AttendanceCorrectionQueueTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Operations', code='OPS')
        self.desig = Designation.objects.create(title='Operations Executive', department=self.dept)
        self.site = Site.objects.create(name='Mumbai Office', code='BOM-1', city='Mumbai')

        self.hr_user = CustomUser.objects.create_user(
            username='hr_attend',
            email='hr_attend@company.com',
            role=CustomUser.Role.HR,
            password='TestPassword123'
        )

        self.emp_user = CustomUser.objects.create_user(
            username='emp_attend',
            email='emp_attend@company.com',
            first_name='Ananya',
            last_name='Deshmukh',
            role=CustomUser.Role.EMPLOYEE,
            password='TestPassword123'
        )
        self.emp_profile = EmployeeProfile.objects.create(
            user=self.emp_user,
            emp_id='EMP990',
            department=self.dept,
            site=self.site,
            joining_date=date(2026, 1, 10),
            bank_name='HDFC',
            bank_account_number='123456789012',
            ifsc_code='HDFC0001234',
            pan_number='ABCDE1234F',
            emergency_contact_phone='9876543210'
        )

        self.correction = AttendanceCorrectionRequest.objects.create(
            employee=self.emp_profile,
            date=date(2026, 11, 8),
            requested_punch_in=timezone.now(),
            requested_punch_out=timezone.now(),
            reason='Missed punch due to biometric machine offline',
            status='PENDING'
        )

    def test_corrections_list_view_renders_only_employee_name(self):
        self.client.force_login(self.hr_user)
        response = self.client.get(reverse('attendance:corrections_list'))
        self.assertEqual(response.status_code, 200)
        # Verify employee full name is displayed
        self.assertContains(response, 'Ananya Deshmukh')
        # Verify employee ID is displayed just below the name
        self.assertContains(response, 'EMP990')
        self.assertNotContains(response, 'EMP990 &bull; Mumbai')
        self.assertNotContains(response, 'EMP990 • Mumbai')
        self.assertContains(response, 'Missed punch due to biometric machine offline')

        # Verify Requested Timing column and Action column are removed from table header
        self.assertNotContains(response, '>Requested Timing</th>')
        self.assertNotContains(response, '>Action</th>')

        # Verify Eye icon button and Detail modal with timing & action buttons are present
        self.assertContains(response, 'bi-eye')
        self.assertContains(response, f'correctionModal{self.correction.id}')
        self.assertContains(response, 'Requested Timing Adjustment')
        self.assertContains(response, 'Approve Request')
        self.assertContains(response, 'Reject Request')

        # Verify Target date gap, pure white table, and pagination footer
        self.assertContains(response, 'style="gap: 8px;"')
        self.assertContains(response, 'id="tablePaginationFooter"')
        self.assertContains(response, 'id="corrPageSizeSelect"')
        self.assertContains(response, 'id="corrPaginationControls"')

        # Verify Sidebar has collapsible Attendance Register grouping
        self.assertContains(response, 'id="attendanceSubmenuHR"')

    def test_approve_attendance_correction(self):
        self.client.force_login(self.hr_user)
        response = self.client.post(
            reverse('attendance:approve_correction', kwargs={'request_id': self.correction.id}),
            {'action': 'APPROVE', 'notes': 'Verified with CCTV'}
        )
        self.assertEqual(response.status_code, 302)
        self.correction.refresh_from_db()
        self.assertEqual(self.correction.status, 'APPROVED')
        self.assertEqual(self.correction.reviewed_by, self.hr_user)

    def test_admin_register_removes_load_button_and_source_column(self):
        self.client.force_login(self.hr_user)
        response = self.client.get(reverse('attendance:admin_register'))
        self.assertEqual(response.status_code, 200)

        # "Load Register" button must be removed
        self.assertNotContains(response, 'Load Register')

        # Dropdowns/inputs must have auto-change submit
        self.assertContains(response, 'onchange="this.form.submit()"')

        # "Source" column must be removed
        self.assertNotContains(response, '<th>Source</th>')

        # Link to whole employee attendance must be present
        detail_url = reverse('attendance:employee_attendance_detail', kwargs={'emp_id': self.emp_profile.emp_id})
        self.assertContains(response, detail_url)

        # Whole row must be clickable to open employee attendance
        self.assertContains(response, 'attendance-clickable-row')
        self.assertContains(response, f"window.location='{detail_url}'")

        # Stats pills must be present on header and interactive
        self.assertContains(response, 'attendance-stat-pill pill-present')
        self.assertContains(response, 'data-status-filter="PRESENT"')
        self.assertContains(response, 'data-status-filter="ABSENT"')
        self.assertContains(response, 'single-attendance-card')

        # Pagination controls and page size selector must be present below table
        self.assertContains(response, 'id="tablePaginationFooter"')
        self.assertContains(response, 'id="pageSizeSelect"')
        self.assertContains(response, 'id="paginationControls"')
        self.assertContains(response, 'id="pageInfoText"')

        # Selected Date: text, calendar icon, branch icon, location icon, and box-arrow icon must be removed
        self.assertNotContains(response, 'Selected Date:')
        self.assertNotContains(response, 'bi-calendar-event')
        self.assertNotContains(response, 'bi-diagram-3')
        self.assertNotContains(response, 'bi-geo-alt')
        self.assertNotContains(response, 'bi-box-arrow-up-right')
        # "All" button must be removed
        self.assertNotContains(response, 'id="filterPillAll"')

        # Distinct attendance table with clear columns
        self.assertContains(response, 'attendance-table')

        # Emp ID column header removed, but Emp ID shown below name
        self.assertNotContains(response, '<th>Emp ID</th>')
        self.assertContains(response, self.emp_profile.emp_id)

        # Designation text like Operations Executive removed
        self.assertNotContains(response, 'Operations Executive')

        # Arrival column header present
        self.assertContains(response, 'Arrival</th>')

        # Department table column removed
        self.assertNotContains(response, '>Department</th>')

        # "Privacy Policy" and "Terms of Employment" must be removed
        self.assertNotContains(response, 'Privacy Policy')
        self.assertNotContains(response, 'Terms of Employment')

    def test_employee_attendance_detail_view(self):
        # Create an attendance record
        Attendance.objects.create(
            employee=self.emp_profile,
            date=date(2026, 11, 1),
            status='PRESENT',
            working_hours=8.5,
            overtime_hours=0.5
        )

        self.client.force_login(self.hr_user)
        response = self.client.get(reverse('attendance:employee_attendance_detail', kwargs={'emp_id': self.emp_profile.emp_id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ananya Deshmukh')
        self.assertContains(response, 'EMP990')
        self.assertContains(response, '8.5')
        self.assertContains(response, 'Back to Daily Register')

    def test_arrival_column_on_time_and_late(self):
        shift = Shift.objects.create(
            name='Office Hours',
            start_time=time(9, 30),
            end_time=time(18, 30),
            grace_period_minutes=0,
            is_default=True
        )

        today = timezone.localdate()
        # Create an on-time attendance (9:20 AM - before 9:30 AM opening)
        att = Attendance.objects.create(
            employee=self.emp_profile,
            date=today,
            shift=shift,
            punch_in=timezone.make_aware(datetime.combine(today, time(9, 20))),
            status='PRESENT',
            is_late=False
        )

        self.client.force_login(self.hr_user)
        response = self.client.get(f"{reverse('attendance:admin_register')}?date={today.strftime('%Y-%m-%d')}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'On Time')

        # Now test late arrival (10:05 AM is late by 35 min after 9:30 AM opening)
        att.is_late = True
        att.punch_in = timezone.make_aware(datetime.combine(today, time(10, 5)))
        att.save()

        response = self.client.get(f"{reverse('attendance:admin_register')}?date={today.strftime('%Y-%m-%d')}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Late by 35 min')

    def test_arrival_column_equal_size_and_placeholder_dash(self):
        self.client.force_login(self.hr_user)
        today = timezone.localdate()
        # Delete any attendance for today to test blank/absent placeholder
        Attendance.objects.filter(employee=self.emp_profile, date=today).delete()

        response = self.client.get(f"{reverse('attendance:admin_register')}?date={today.strftime('%Y-%m-%d')}")
        self.assertEqual(response.status_code, 200)
        # Verify placeholder '--' is rendered for unpunched/absent employee
        self.assertContains(response, '<span class="text-muted">--</span>')

        # Now create an on-time record and verify width: 115px
        shift = Shift.objects.create(name='Office Hours', start_time=time(9, 30), end_time=time(18, 30), is_default=False)
        att = Attendance.objects.create(
            employee=self.emp_profile,
            date=today,
            shift=shift,
            punch_in=timezone.make_aware(datetime.combine(today, time(9, 30))),
            status='PRESENT',
            is_late=False
        )
        response = self.client.get(f"{reverse('attendance:admin_register')}?date={today.strftime('%Y-%m-%d')}")
        self.assertContains(response, 'width: 115px')
        self.assertContains(response, 'On Time')

    def test_punch_lifecycle_strict_rules(self):
        """
        Tests the strict one punch-in and one punch-out rule per day:
        1. Cannot punch out before punching in.
        2. Can punch in once.
        3. Cannot punch in twice.
        4. Can punch out once.
        5. Cannot punch in after punching out.
        6. Cannot punch out twice.
        """
        today = timezone.localdate()
        Attendance.objects.filter(employee=self.emp_profile, date=today).delete()
        self.client.force_login(self.emp_user)

        # 1. Cannot punch out before punch in
        res1 = self.client.get(reverse('attendance:punch_out'), follow=True)
        self.assertContains(res1, "You have not punched in today yet! Punch in is required before you can punch out.")
        self.assertIsNone(Attendance.objects.filter(employee=self.emp_profile, date=today).first())

        # 2. Punch in succeeds
        res2 = self.client.get(reverse('attendance:punch_in'), follow=True)
        self.assertContains(res2, "Punch In successful")
        att = Attendance.objects.get(employee=self.emp_profile, date=today)
        self.assertIsNotNone(att.punch_in)
        self.assertIsNone(att.punch_out)

        # 3. Cannot punch in again
        res3 = self.client.get(reverse('attendance:punch_in'), follow=True)
        self.assertContains(res3, "You are already punched in today")

        # 4. Punch out succeeds
        res4 = self.client.get(reverse('attendance:punch_out'), follow=True)
        self.assertContains(res4, "Punch Out successful")
        att.refresh_from_db()
        self.assertIsNotNone(att.punch_out)

        # 5. Cannot punch in after punch out
        res5 = self.client.get(reverse('attendance:punch_in'), follow=True)
        self.assertContains(res5, "You have already punched out for today")
        self.assertContains(res5, "Only one punch-in and punch-out is allowed per day")

        # 6. Cannot punch out twice
        res6 = self.client.get(reverse('attendance:punch_out'), follow=True)
        self.assertContains(res6, "You have already punched out today")
        self.assertContains(res6, "Only one punch-out is permitted per day")

    def test_ui_punch_buttons_disabled_states(self):
        today = timezone.localdate()
        Attendance.objects.filter(employee=self.emp_profile, date=today).delete()
        self.client.force_login(self.emp_user)

        # Before punch in: Punch Out button disabled in topbar & dashboard
        res_dash = self.client.get(reverse('portal:dashboard_employee'))
        self.assertEqual(res_dash.status_code, 200)
        self.assertContains(res_dash, 'Punch In required before you can Punch Out')

        # After punch in: Punch Out is enabled, Punch In disabled
        self.client.get(reverse('attendance:punch_in'))
        res_dash2 = self.client.get(reverse('portal:dashboard_employee'))
        self.assertEqual(res_dash2.status_code, 200)
        self.assertContains(res_dash2, 'Already Punched In')

        # After punch out: both buttons disabled, no 'Done (2h)' or 'Day Completed' badge
        self.client.get(reverse('attendance:punch_out'))
        res_dash3 = self.client.get(reverse('portal:dashboard_employee'))
        self.assertEqual(res_dash3.status_code, 200)
        self.assertNotContains(res_dash3, 'Day Completed')
        self.assertNotContains(res_dash3, 'Done (')
        self.assertContains(res_dash3, 'Already punched out for today')
