import json
from unittest.mock import patch
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import date, time, datetime
from accounts.models import CustomUser
from employees.models import EmployeeProfile
from organization.models import Department, Designation, Site
from attendance.models import AttendanceCorrectionRequest, Attendance, Shift, QRCodeScanLog


class AttendanceCorrectionQueueTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Operations', code='OPS')
        self.desig = Designation.objects.create(title='Operations Executive', department=self.dept)
        self.site = Site.objects.create(name='Mumbai Office', code='BOM-1', city='Mumbai')

        self.head_user = CustomUser.objects.create_user(
            username='head_attend',
            email='head_attend@company.com',
            role=CustomUser.Role.HEAD,
            password='TestPassword123'
        )

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

        # Before punch in: Direct punch buttons removed; shifted to Dynamic QR Scanner button
        res_dash = self.client.get(reverse('portal:dashboard_employee'))
        self.assertEqual(res_dash.status_code, 200)
        self.assertContains(res_dash, 'Scan Dynamic QR')
        self.assertContains(res_dash, 'Scan QR to Punch')
        self.assertContains(res_dash, 'Not Punched In')
        self.assertNotContains(res_dash, 'Punch In required before you can Punch Out')

        # After punch in: Topbar shows Punch In time and dashboard shows Present
        self.client.get(reverse('attendance:punch_in'))
        res_dash2 = self.client.get(reverse('portal:dashboard_employee'))
        self.assertEqual(res_dash2.status_code, 200)
        self.assertContains(res_dash2, 'Scan Dynamic QR')
        self.assertContains(res_dash2, 'Present')

        # After punch out: Topbar shows Done and dashboard shows Punched Out
        self.client.get(reverse('attendance:punch_out'))
        res_dash3 = self.client.get(reverse('portal:dashboard_employee'))
        self.assertEqual(res_dash3.status_code, 200)
        self.assertContains(res_dash3, 'Punched Out')
        self.assertContains(res_dash3, 'Done (')


class DynamicQRAttendanceTests(TestCase):
    """
    Comprehensive test suite for Dynamic QR Attendance System:
    - 5-second dynamic cryptographic rotation
    - Punch In & Punch Out modes
    - Location Security (Strict Device GPS Geofencing 200m)
    - Kiosk Terminal and Scanner API endpoints
    """

    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Engineering', code='ENG')
        self.desig = Designation.objects.create(title='Software Engineer', department=self.dept)

        # Office Site: Bangalore HQ (Lat: 12.9716, Lng: 77.5946, Geofence: 200m)
        self.site = Site.objects.create(
            name='Bengaluru HQ Tech Park',
            code='BLR-HQ',
            city='Bengaluru',
            latitude=12.971598,
            longitude=77.594562,
            geofence_radius_meters=200,
            qr_rotation_seconds=4,
            is_qr_attendance_enabled=True,
        )

        self.user = CustomUser.objects.create_user(
            username='rohit_dev',
            email='rohit@company.com',
            first_name='Rohit',
            last_name='Verma',
            role=CustomUser.Role.EMPLOYEE,
            password='TestPassword123'
        )
        self.emp = EmployeeProfile.objects.create(
            user=self.user,
            emp_id='EMP501',
            department=self.dept,
            site=self.site,
            joining_date=date(2026, 1, 1),
            bank_name='SBI',
            bank_account_number='987654321098',
            ifsc_code='SBIN0001234',
            pan_number='ABCDE5678F',
            emergency_contact_phone='9876543210'
        )

        self.user2 = CustomUser.objects.create_user(
            username='neha_dev',
            email='neha@company.com',
            first_name='Neha',
            last_name='Sharma',
            role=CustomUser.Role.EMPLOYEE,
            password='TestPassword123'
        )
        self.emp2 = EmployeeProfile.objects.create(
            user=self.user2,
            emp_id='EMP502',
            department=self.dept,
            site=self.site,
            joining_date=date(2026, 1, 1),
            bank_name='HDFC',
            bank_account_number='123456789012',
            ifsc_code='HDFC0001234',
            pan_number='PQRST1234G',
            emergency_contact_phone='9876543211'
        )

        self.hr_user = CustomUser.objects.create_user(
            username='hr_qr_admin',
            email='hr_qr@company.com',
            role=CustomUser.Role.HR,
            password='TestPassword123'
        )
        self.head_user = CustomUser.objects.create_user(
            username='head_qr_admin',
            email='head_qr@company.com',
            role=CustomUser.Role.HEAD,
            password='TestPassword123'
        )
        from organization.models import MasterDataPermission
        MasterDataPermission.objects.update_or_create(
            singleton_id=1,
            defaults={'allow_all_hr': True, 'can_manage_locations': True}
        )

        self.shift = Shift.objects.create(
            name='General Shift',
            start_time=time(9, 30),
            end_time=time(18, 30),
            grace_period_minutes=15,
            is_default=True
        )

    def test_dynamic_qr_payload_generation_4_seconds(self):
        from attendance.qr_services import generate_dynamic_qr_payload
        payload = generate_dynamic_qr_payload(self.site)

        self.assertIn('token', payload)
        self.assertIn('slot', payload)
        self.assertIn('qr_image_base64', payload)
        self.assertTrue(payload['qr_image_base64'].startswith('data:image/png;base64,'))
        self.assertEqual(payload['rotation_seconds'], 4)
        self.assertTrue(0.0 <= payload['countdown_seconds'] <= 4.0)

    def test_dynamic_qr_token_validation_and_expiry_4_seconds(self):
        import time as py_time
        from attendance.qr_services import generate_dynamic_qr_payload, validate_dynamic_qr_token

        # Valid fresh token in current 4s slot
        payload = generate_dynamic_qr_payload(self.site)
        token = payload['token']
        is_valid, status, err, age = validate_dynamic_qr_token(self.site, token)
        self.assertTrue(is_valid)
        self.assertEqual(status, 'VALID')
        self.assertIsNone(err)

        # Expired token (simulate 10 seconds ago = 2 slots ago)
        old_slot = int((py_time.time() - 10) // 4)
        import hmac, hashlib
        secret = self.site.get_qr_secret_key()
        msg = f"{self.site.id}:{old_slot}".encode('utf-8')
        sig = hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()[:16]
        expired_token = f"{self.site.id}:{old_slot}:{sig}"

        is_valid_exp, status_exp, err_exp, age_exp = validate_dynamic_qr_token(self.site, expired_token)
        self.assertFalse(is_valid_exp)
        self.assertEqual(status_exp, 'EXPIRED_QR')
        self.assertIn('exceeds 4s dynamic limit', err_exp)

        # Forged/Tampered token
        tampered_token = f"{self.site.id}:{payload['slot']}:badsignature123"
        is_valid_tamp, status_tamp, err_tamp, _ = validate_dynamic_qr_token(self.site, tampered_token)
        self.assertFalse(is_valid_tamp)
        self.assertEqual(status_tamp, 'INVALID_TOKEN')

    def test_location_security_gps_geofence_200m(self):
        # 1. Coordinate within 50 meters of Bangalore HQ (12.971598, 77.594562)
        within_lat = 12.971800
        within_lng = 77.594700
        is_verified, dist, msg = self.site.is_gps_verified(within_lat, within_lng)
        self.assertTrue(is_verified)
        self.assertLess(dist, 200)

        # 2. Coordinate far away (e.g. 500 meters or kilometers away)
        far_lat = 12.980000
        far_lng = 77.605000
        is_verified_far, dist_far, msg_far = self.site.is_gps_verified(far_lat, far_lng)
        self.assertFalse(is_verified_far)
        self.assertGreater(dist_far, 200)

    def test_single_use_slot_anti_screenshot_enforcement(self):
        """
        Tests that each 4-second QR slot can only be scanned by ONE employee.
        If a screenshot is forwarded to a second employee, the second scan fails.
        """
        import json
        from attendance.qr_services import generate_dynamic_qr_payload

        today = timezone.localdate()
        Attendance.objects.filter(date=today).delete()

        with patch('attendance.qr_services.time.time') as mock_time:
            mock_time.return_value = 1700000000.0
            payload = generate_dynamic_qr_payload(self.site)
            shared_token = payload['token']

            # Employee 1 punches successfully within the 4s slot
            mock_time.return_value = 1700000000.5
            self.client.force_login(self.user)
            res1 = self.client.post(
                reverse('attendance:qr_punch_api'),
                data=json.dumps({
                    'site_id': self.site.id,
                    'token': shared_token,
                    'latitude': 12.971600,
                    'longitude': 77.594560,
                    'punch_mode': 'AUTO',
                }),
                content_type='application/json'
            )
            self.assertEqual(res1.status_code, 200)
            self.assertTrue(res1.json()['success'])

            # Employee 2 attempts to use the same token/screenshot in that slot
            mock_time.return_value = 1700000001.0
            self.client.force_login(self.user2)
            res2 = self.client.post(
                reverse('attendance:qr_punch_api'),
                data=json.dumps({
                    'site_id': self.site.id,
                    'token': shared_token,
                    'latitude': 12.971600,
                    'longitude': 77.594560,
                    'punch_mode': 'AUTO',
                }),
                content_type='application/json'
            )
            self.assertEqual(res2.status_code, 200)
            data2 = res2.json()
            self.assertFalse(data2['success'])
            self.assertEqual(data2['status'], 'SLOT_ALREADY_USED')
            self.assertIn('already been scanned', data2['message'])

    def test_gps_required_when_location_turned_off(self):
        """
        When employee device location / GPS is turned off (latitude=None), punch must be rejected.
        """
        import json
        from attendance.qr_services import generate_dynamic_qr_payload

        self.client.force_login(self.user)
        payload = generate_dynamic_qr_payload(self.site)

        res = self.client.post(
            reverse('attendance:qr_punch_api'),
            data=json.dumps({
                'site_id': self.site.id,
                'token': payload['token'],
                'latitude': None,
                'longitude': None,
                'punch_mode': 'AUTO',
            }),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['status'], 'GPS_REQUIRED')
        self.assertIn('Location (GPS) Required', data['title'])

    def test_qr_punch_api_punch_in_and_punch_out_flow(self):
        import json
        from unittest.mock import patch
        from attendance.qr_services import generate_dynamic_qr_payload

        self.client.force_login(self.user)
        today = timezone.localdate()
        Attendance.objects.filter(employee=self.emp, date=today).delete()

        with patch('attendance.qr_services.time.time') as mock_time:
            # 1. Execute Punch In at t0
            mock_time.return_value = 1700000000.0
            payload = generate_dynamic_qr_payload(self.site)

            response = self.client.post(
                reverse('attendance:qr_punch_api'),
                data=json.dumps({
                    'site_id': self.site.id,
                    'token': payload['token'],
                    'latitude': 12.971600,
                    'longitude': 77.594560,
                    'punch_mode': 'AUTO',
                }),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200)
            res_data = response.json()
            self.assertTrue(res_data['success'])
            self.assertEqual(res_data['action'], 'PUNCH_IN')
            self.assertIn('Punch In Successful', res_data['title'])

            # Verify Attendance in DB
            att = Attendance.objects.get(employee=self.emp, date=today)
            self.assertIsNotNone(att.punch_in)
            self.assertIsNone(att.punch_out)
            self.assertEqual(att.device_source, 'QR_KIOSK')
            self.assertTrue(att.location_verified)

            # 2. Cannot Punch In again (advance slot to t0 + 4.1s)
            mock_time.return_value = 1700000004.1
            payload2 = generate_dynamic_qr_payload(self.site)

            response_dup = self.client.post(
                reverse('attendance:qr_punch_api'),
                data=json.dumps({
                    'site_id': self.site.id,
                    'token': payload2['token'],
                    'latitude': 12.971600,
                    'longitude': 77.594560,
                    'punch_mode': 'IN',
                }),
                content_type='application/json'
            )
            self.assertEqual(response_dup.status_code, 200)
            self.assertFalse(response_dup.json()['success'])
            self.assertEqual(response_dup.json()['status'], 'ALREADY_PUNCHED_IN')

            # 3. Execute Punch Out via API (advance slot to t0 + 8.2s)
            mock_time.return_value = 1700000008.2
            payload3 = generate_dynamic_qr_payload(self.site)

            response_out = self.client.post(
                reverse('attendance:qr_punch_api'),
                data=json.dumps({
                    'site_id': self.site.id,
                    'token': payload3['token'],
                    'latitude': 12.971600,
                    'longitude': 77.594560,
                    'punch_mode': 'AUTO',
                }),
                content_type='application/json'
            )
            self.assertEqual(response_out.status_code, 200)
            res_data_out = response_out.json()
            self.assertTrue(res_data_out['success'])
            self.assertEqual(res_data_out['action'], 'PUNCH_OUT')
            self.assertIn('Punch Out Successful', res_data_out['title'])

            att.refresh_from_db()
            self.assertIsNotNone(att.punch_out)
            self.assertGreaterEqual(att.working_hours, 0)

            # 4. Day is complete - subsequent punch reports ALREADY_COMPLETED (advance to t0 + 12.3s)
            mock_time.return_value = 1700000012.3
            payload4 = generate_dynamic_qr_payload(self.site)

            response_comp = self.client.post(
                reverse('attendance:qr_punch_api'),
                data=json.dumps({
                    'site_id': self.site.id,
                    'token': payload4['token'],
                    'latitude': 12.971600,
                    'longitude': 77.594560,
                    'punch_mode': 'AUTO',
                }),
                content_type='application/json'
            )
            self.assertEqual(response_comp.status_code, 200)
            self.assertFalse(response_comp.json()['success'])
            self.assertEqual(response_comp.json()['status'], 'ALREADY_COMPLETED')

    def test_qr_kiosk_view_and_token_api(self):
        self.client.force_login(self.hr_user)

        # Kiosk terminal page
        res = self.client.get(reverse('attendance:qr_kiosk'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Dynamic Attendance Terminal')
        self.assertContains(res, 'Dynamic 4s Rotation')
        self.assertContains(res, 'PUNCH IN')
        self.assertContains(res, 'PUNCH OUT')

        # Token API polled every 4s
        res_api = self.client.get(reverse('attendance:qr_kiosk_token_api', kwargs={'site_id': self.site.id}))
        self.assertEqual(res_api.status_code, 200)
        data = res_api.json()
        self.assertTrue(data['success'])
        self.assertIn('qr_image_base64', data['payload'])
        self.assertEqual(data['payload']['rotation_seconds'], 4)

    def test_qr_scanner_view(self):
        self.client.force_login(self.user)
        res = self.client.get(reverse('attendance:qr_scanner'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Dynamic QR Attendance Scanner')
        self.assertContains(res, 'Auto-Detect')
        self.assertContains(res, 'Punch In')
        self.assertContains(res, 'Punch Out')
        self.assertContains(res, 'Acquiring GPS')
        # Verify Open Entrance Kiosk button is hidden for normal employees
        self.assertNotContains(res, 'Open Entrance Kiosk')

        # Verify Open Entrance Kiosk button is hidden for HR
        self.client.force_login(self.hr_user)
        res_hr = self.client.get(reverse('attendance:qr_scanner'))
        self.assertNotContains(res_hr, 'Open Entrance Kiosk')

        # Verify Open Entrance Kiosk button is visible to Head / Admin
        self.client.force_login(self.head_user)
        res_head = self.client.get(reverse('attendance:qr_scanner'))
        self.assertContains(res_head, 'Open Entrance Kiosk')

    def test_qr_dashboard_view_and_site_config(self):
        import json
        # 1. Verify access control: HR and Employee get 403 Forbidden
        self.client.force_login(self.hr_user)
        res_hr = self.client.get(reverse('attendance:qr_dashboard'))
        self.assertEqual(res_hr.status_code, 403)

        self.client.force_login(self.user)
        res_emp = self.client.get(reverse('attendance:qr_dashboard'))
        self.assertEqual(res_emp.status_code, 403)

        # 2. Head / Admin user gets 200 OK
        self.client.force_login(self.head_user)
        res = self.client.get(reverse('attendance:qr_dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Dynamic QR Attendance & Security Hub')
        self.assertContains(res, 'Office Sites & Geofencing Parameters')
        self.assertContains(res, 'Share Kiosk Link')

        # Site location config API (Admin only)
        res_config = self.client.post(
            reverse('attendance:site_location_config_api', kwargs={'site_id': self.site.id}),
            data=json.dumps({
                'latitude': '12.980000',
                'longitude': '77.600000',
                'geofence_radius_meters': 200,
                'qr_rotation_seconds': 4,
            }),
            content_type='application/json'
        )
        self.assertEqual(res_config.status_code, 200)
        self.assertTrue(res_config.json()['success'])
        self.site.refresh_from_db()
        self.assertEqual(float(self.site.latitude), 12.98)
        self.assertEqual(self.site.geofence_radius_meters, 200)

        # 3. Dedicated Entrance Kiosk terminal link access (without user login)
        self.client.logout()
        secret_key = self.site.get_qr_secret_key()

        # Unauthenticated request without terminal_key redirects to login
        res_kiosk_anon = self.client.get(reverse('attendance:qr_kiosk_site', kwargs={'site_id': self.site.id}))
        self.assertEqual(res_kiosk_anon.status_code, 302)

        # Device opens with terminal_key -> 200 OK with dynamic QR
        res_kiosk_device = self.client.get(
            reverse('attendance:qr_kiosk_site', kwargs={'site_id': self.site.id}),
            {'terminal_key': secret_key}
        )
        self.assertEqual(res_kiosk_device.status_code, 200)
        self.assertContains(res_kiosk_device, 'Live Kiosk Active')

        # Device polls rotating token API with terminal_key -> 200 OK
        res_token = self.client.get(
            reverse('attendance:qr_kiosk_token_api', kwargs={'site_id': self.site.id}),
            {'terminal_key': secret_key}
        )
        self.assertEqual(res_token.status_code, 200)
        self.assertTrue(res_token.json()['success'])
        self.assertIn('payload', res_token.json())

    def test_master_data_location_create_with_gps(self):
        """
        Verify that Master Data location_create and location_edit save latitude, longitude, and geofence.
        """
        self.client.force_login(self.hr_user)
        res_create = self.client.post(
            reverse('organization:location_create'),
            {
                'name': 'Pune Development Center',
                'city': 'Pune',
                'code': 'PUN-01',
                'address': 'Hinjawadi Phase 1',
                'contact_phone': '9876543210',
                'latitude': '18.591234',
                'longitude': '73.738765',
                'geofence_radius_meters': '200',
            }
        )
        self.assertEqual(res_create.status_code, 302)
        new_site = Site.objects.filter(code='PUN-01').first()
        self.assertIsNotNone(new_site)
        self.assertEqual(float(new_site.latitude), 18.591234)
        self.assertEqual(float(new_site.longitude), 73.738765)
        self.assertEqual(new_site.geofence_radius_meters, 200)

        # Edit location
        res_edit = self.client.post(
            reverse('organization:location_edit', kwargs={'site_id': new_site.id}),
            {
                'name': 'Pune Innovation Center',
                'city': 'Pune',
                'code': 'PUN-01',
                'address': 'Hinjawadi Phase 2',
                'contact_phone': '9876543210',
                'latitude': '18.595000',
                'longitude': '73.740000',
                'geofence_radius_meters': '250',
                'is_active': 'on'
            }
        )
        self.assertEqual(res_edit.status_code, 302)
        new_site.refresh_from_db()
        self.assertEqual(new_site.name, 'Pune Innovation Center')
        self.assertEqual(float(new_site.latitude), 18.595)
        self.assertEqual(new_site.geofence_radius_meters, 250)

    def test_qr_kiosk_token_api_recent_punches(self):
        """
        Verify that qr_kiosk_token_api returns recent successful punches for live pop-up toast.
        """
        self.client.force_login(self.hr_user)

        # 1. Initially no recent scans
        res = self.client.get(reverse('attendance:qr_kiosk_token_api', kwargs={'site_id': self.site.id}))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertIn('recent_punches', data)
        self.assertEqual(len(data['recent_punches']), 0)

        # 2. Add a successful punch scan log
        QRCodeScanLog.objects.create(
            site=self.site,
            employee=self.emp,
            actual_punch_type='IN',
            status='SUCCESS',
            token_str='test-token-123',
            slot_index=100
        )

        res2 = self.client.get(reverse('attendance:qr_kiosk_token_api', kwargs={'site_id': self.site.id}))
        data2 = res2.json()
        self.assertEqual(len(data2['recent_punches']), 1)
        punch = data2['recent_punches'][0]
        self.assertEqual(punch['employee_name'], self.emp.full_name)
        self.assertEqual(punch['punch_label'], 'Punch In')
        self.assertEqual(punch['punch_type'], 'IN')

    def test_qr_punch_reflects_in_attendance_register(self):
        """
        Verify that when an employee punches via QR, their record is reflected in Daily Attendance Register.
        """
        from unittest.mock import patch
        from attendance.qr_services import generate_dynamic_qr_payload

        self.client.force_login(self.user)
        today = timezone.localdate()
        Attendance.objects.filter(employee=self.emp, date=today).delete()

        with patch('attendance.qr_services.time.time') as mock_time:
            mock_time.return_value = 1700000000.0
            payload = generate_dynamic_qr_payload(self.site)

            res = self.client.post(
                reverse('attendance:qr_punch_api'),
                data=json.dumps({
                    'token': payload['token'],
                    'site_id': self.site.id,
                    'latitude': 12.971598,
                    'longitude': 77.594562,
                    'punch_mode': 'AUTO',
                }),
                content_type='application/json'
            )
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.json()['success'])

        # Now view Daily Attendance Register as HR
        self.client.force_login(self.hr_user)
        res_reg = self.client.get(reverse('attendance:admin_register'))
        self.assertEqual(res_reg.status_code, 200)
        self.assertContains(res_reg, self.emp.full_name)
        self.assertContains(res_reg, 'Present')
        self.assertContains(res_reg, 'Live Kiosk Sync')



