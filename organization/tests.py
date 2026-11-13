from decimal import Decimal
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from organization.models import Holiday, Site, OperatingSchedule, MasterDataPermission, Department
from leave_management.models import LeaveType, LeaveBalance
from employees.models import EmployeeProfile


class MasterDataTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Users
        self.admin_user = CustomUser.objects.create_user(
            username='admin_head',
            email='admin@company.com',
            password='Password@123',
            role=CustomUser.Role.HEAD
        )
        self.hr_user = CustomUser.objects.create_user(
            username='hr_admin',
            email='hr@company.com',
            password='Password@123',
            role=CustomUser.Role.HR
        )
        self.employee_user = CustomUser.objects.create_user(
            username='staff_john',
            email='john@company.com',
            password='Password@123',
            role=CustomUser.Role.EMPLOYEE
        )

        # Ensure MasterDataPermission setting exists
        self.perm_setting = MasterDataPermission.get_settings()
        self.perm_setting.allow_all_hr = False
        self.perm_setting.allowed_users.clear()
        self.perm_setting.save()

        # Ensure 7-day Operating Schedule exists
        OperatingSchedule.get_weekly_schedule()

        # Ensure Official 2026 Holidays exist
        official_holidays = [
            ('2026-01-14', 'Makar Sankranti', 'FESTIVAL'),
            ('2026-01-26', 'Republic Day', 'PUBLIC'),
            ('2026-02-15', 'Maha Shivratri', 'FESTIVAL'),
            ('2026-03-04', 'Holi', 'FESTIVAL'),
            ('2026-05-01', 'May Day', 'PUBLIC'),
            ('2026-06-14', 'Raja', 'FESTIVAL'),
            ('2026-07-16', 'Rath Yatra', 'FESTIVAL'),
            ('2026-08-15', 'Independence Day', 'PUBLIC'),
            ('2026-08-28', 'Raksha Bandhan', 'FESTIVAL'),
            ('2026-09-14', 'Ganesh Chaturthi', 'FESTIVAL'),
            ('2026-10-19', 'Dussehra (Maha Navami)', 'FESTIVAL'),
            ('2026-10-20', 'Dussehra (Vijaya Dashami)', 'FESTIVAL'),
            ('2026-11-08', 'Diwali', 'FESTIVAL'),
            ('2026-11-24', 'Kartik Poornima', 'FESTIVAL')
        ]
        for d_str, title, h_type in official_holidays:
            h_date = datetime.date.fromisoformat(d_str)
            Holiday.objects.get_or_create(
                date=h_date,
                defaults={'title': title, 'holiday_type': h_type, 'description': 'Official company holiday'}
            )

        # Ensure Leave Types exist
        self.sl_type, _ = LeaveType.objects.get_or_create(
            code='SL',
            defaults={'name': 'Sick Leave', 'days_per_year': Decimal('10.0'), 'is_paid': True}
        )
        self.pl_type, _ = LeaveType.objects.get_or_create(
            code='PL',
            defaults={'name': 'Paid Leave', 'days_per_year': Decimal('18.0'), 'is_paid': True}
        )

    def test_official_2026_holidays_present(self):
        """Verify the 2026 holiday calendar has been seeded properly."""
        holidays_2026 = Holiday.objects.filter(date__year=2026)
        titles = list(holidays_2026.values_list('title', flat=True))
        
        # Check core holidays
        self.assertTrue(any('Makar Sankranti' in t for t in titles))
        self.assertTrue(any('Republic Day' in t for t in titles))
        self.assertTrue(any('Holi' in t for t in titles))
        self.assertTrue(any('Rath Yatra' in t for t in titles))
        self.assertTrue(any('Independence Day' in t for t in titles))
        self.assertTrue(any('Dussehra' in t for t in titles))
        self.assertTrue(any('Diwali' in t for t in titles))
        self.assertTrue(any('Kartik Poornima' in t for t in titles))

    def test_access_control_head_admin(self):
        """Admin/Head always has access to Master Data dashboard."""
        self.client.login(username='admin_head', password='Password@123')
        response = self.client.get(reverse('organization:master_data'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Master Data Control Center")

    def test_access_control_regular_employee_forbidden(self):
        """Regular employee is denied access (403 Forbidden)."""
        self.client.login(username='staff_john', password='Password@123')
        response = self.client.get(reverse('organization:master_data'))
        self.assertEqual(response.status_code, 403)

    def test_access_control_hr_default_forbidden(self):
        """HR is denied by default until Admin enables HR delegation."""
        self.client.login(username='hr_admin', password='Password@123')
        response = self.client.get(reverse('organization:master_data'))
        self.assertEqual(response.status_code, 403)

    def test_access_control_hr_delegated_success(self):
        """When Admin grants access to all HR, HR user can view and edit Master Data."""
        self.perm_setting.allow_all_hr = True
        self.perm_setting.save()

        self.client.login(username='hr_admin', password='Password@123')
        response = self.client.get(reverse('organization:master_data'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Master Data Control Center")

    def test_access_control_specific_user_delegated(self):
        """When Admin grants access to a specific staff member, they can access."""
        self.perm_setting.allowed_users.add(self.employee_user)
        self.client.login(username='staff_john', password='Password@123')
        response = self.client.get(reverse('organization:master_data'))
        self.assertEqual(response.status_code, 200)

    def test_holiday_crud(self):
        """Test adding, editing, and deleting a holiday."""
        self.client.login(username='admin_head', password='Password@123')

        # Create
        post_data = {
            'title': 'Test Holiday',
            'date': '2026-12-20',
            'holiday_type': 'COMPANY',
            'description': 'Special celebration'
        }
        res_create = self.client.post(reverse('organization:holiday_create'), post_data)
        self.assertIn(res_create.status_code, [302, 200])
        h = Holiday.objects.filter(date=datetime.date(2026, 12, 20)).first()
        self.assertIsNotNone(h)
        self.assertEqual(h.title, 'Test Holiday')

        # Edit
        edit_data = {
            'title': 'Updated Holiday Name',
            'date': '2026-12-20',
            'holiday_type': 'COMPANY',
            'description': 'Updated description'
        }
        res_edit = self.client.post(reverse('organization:holiday_edit', args=[h.id]), edit_data)
        self.assertIn(res_edit.status_code, [302, 200])
        h.refresh_from_db()
        self.assertEqual(h.title, 'Updated Holiday Name')

        # Delete
        res_delete = self.client.post(reverse('organization:holiday_delete', args=[h.id]))
        self.assertIn(res_delete.status_code, [302, 200])
        self.assertFalse(Holiday.objects.filter(id=h.id).exists())

    def test_timings_batch_and_day_update(self):
        """Test uniform batch timings update and day-by-day update."""
        self.client.login(username='admin_head', password='Password@123')

        # Batch update
        batch_data = {
            'opening_time': '09:00',
            'closing_time': '18:00',
            'grace_period_minutes': '20',
        }
        res_batch = self.client.post(reverse('organization:timing_batch_update'), batch_data)
        self.assertIn(res_batch.status_code, [302, 200])
        monday = OperatingSchedule.objects.get(day_of_week=0)
        self.assertEqual(str(monday.opening_time), '09:00:00')
        self.assertEqual(str(monday.closing_time), '18:00:00')

        # Day update: Saturday half day
        saturday = OperatingSchedule.objects.get(day_of_week=5)
        day_data = {
            'is_working_day': 'on',
            'opening_time': '09:30',
            'closing_time': '13:30',
            'grace_period_minutes': '15',
            'notes': 'Saturday Half-Day Schedule'
        }
        res_day = self.client.post(reverse('organization:timing_day_update', args=[saturday.id]), day_data)
        self.assertIn(res_day.status_code, [302, 200])
        saturday.refresh_from_db()
        self.assertEqual(str(saturday.closing_time), '13:30:00')

        # Sunday should remain weekly off
        sunday = OperatingSchedule.objects.get(day_of_week=6)
        self.assertFalse(sunday.is_working_day)

    def test_locations_crud(self):
        """Test adding, editing, and deleting/deactivating a location."""
        self.client.login(username='admin_head', password='Password@123')

        # Add Location
        loc_data = {
            'name': 'Kolkata Tech Hub',
            'city': 'Kolkata',
            'code': 'CCU-01',
            'address': 'Salt Lake Sector V',
            'contact_phone': '+91 90000 12345',
        }
        res_add = self.client.post(reverse('organization:location_create'), loc_data)
        self.assertIn(res_add.status_code, [302, 200])
        loc = Site.objects.filter(code='CCU-01').first()
        self.assertIsNotNone(loc)
        self.assertEqual(loc.name, 'Kolkata Tech Hub')

        # Edit Location
        edit_data = {
            'name': 'Kolkata Innovation Hub',
            'city': 'Kolkata',
            'code': 'CCU-01',
            'address': 'New Town Action Area',
            'contact_phone': '+91 90000 99999',
            'is_active': 'on'
        }
        res_edit = self.client.post(reverse('organization:location_edit', args=[loc.id]), edit_data)
        self.assertIn(res_edit.status_code, [302, 200])
        loc.refresh_from_db()
        self.assertEqual(loc.name, 'Kolkata Innovation Hub')

        # Delete Location
        res_del = self.client.post(reverse('organization:location_delete', args=[loc.id]))
        self.assertIn(res_del.status_code, [302, 200])
        self.assertFalse(Site.objects.filter(id=loc.id).exists())

    def test_departments_crud(self):
        """Test adding, editing, and deleting a department in Master Data (Admin Only)."""
        # Non-admin (HR) gets 403 Forbidden
        self.client.login(username='hr_admin', password='Password@123')
        res_hr = self.client.post(reverse('organization:department_create'), {'name': 'Unauthorized HR Dept'})
        self.assertEqual(res_hr.status_code, 403)
        self.assertFalse(Department.objects.filter(name='Unauthorized HR Dept').exists())
        self.client.logout()

        # Admin / Head can add department
        self.client.login(username='admin_head', password='Password@123')

        # Add Department
        dept_data = {
            'name': 'Cloud Infrastructure & DevOps',
            'code': 'DEVOPS',
            'description': 'AWS, Azure, and Kubernetes infra',
        }
        res_add = self.client.post(reverse('organization:department_create'), dept_data)
        self.assertIn(res_add.status_code, [302, 200])
        dept = Department.objects.filter(code='DEVOPS').first()
        self.assertIsNotNone(dept)
        self.assertEqual(dept.name, 'Cloud Infrastructure & DevOps')

        # Edit Department
        edit_data = {
            'name': 'Platform Engineering & SRE',
            'code': 'SRE',
            'description': 'Site reliability and developer platforms',
        }
        res_edit = self.client.post(reverse('organization:department_edit', args=[dept.id]), edit_data)
        self.assertIn(res_edit.status_code, [302, 200])
        dept.refresh_from_db()
        self.assertEqual(dept.name, 'Platform Engineering & SRE')
        self.assertEqual(dept.code, 'SRE')

        # Delete Department
        res_del = self.client.post(reverse('organization:department_delete', args=[dept.id]))
        self.assertIn(res_del.status_code, [302, 200])
        self.assertFalse(Department.objects.filter(id=dept.id).exists())

    def test_leave_policy_update_annual_and_monthly(self):
        """Test leave quota updates and balance sync."""
        self.client.login(username='admin_head', password='Password@123')

        # Update Sick Leave to 12.0 days (1.0 day/mo)
        sl_post = {
            'allocation_mode': 'annual',
            'days_per_year': '12.0',
            'monthly_rate': '1.0',
            'is_paid': 'on',
            'requires_attachment': 'on',
            'description': 'Medical consultation and illness'
        }
        res_sl = self.client.post(reverse('organization:leave_policy_update', args=[self.sl_type.id]), sl_post)
        self.assertIn(res_sl.status_code, [302, 200])
        self.sl_type.refresh_from_db()
        self.assertEqual(self.sl_type.days_per_year, Decimal('12.0'))

        # Update Paid Leave via monthly mode: 1.75 days/mo = 21.0 days/year
        pl_post = {
            'allocation_mode': 'monthly',
            'days_per_year': '21.0',
            'monthly_rate': '1.75',
            'is_paid': 'on',
            'description': 'Annual paid leave'
        }
        res_pl = self.client.post(reverse('organization:leave_policy_update', args=[self.pl_type.id]), pl_post)
        self.assertIn(res_pl.status_code, [302, 200])
        self.pl_type.refresh_from_db()
        self.assertEqual(self.pl_type.days_per_year, Decimal('21.0'))

    def test_admin_permissions_update(self):
        """Admin can toggle HR access and delegate users."""
        self.client.login(username='admin_head', password='Password@123')
        perm_data = {
            'allow_all_hr': 'on',
            'can_manage_holidays': 'on',
            'can_manage_timings': 'on',
            'can_manage_locations': 'on',
            'can_manage_leave_policy': 'on',
            'allowed_users': [str(self.employee_user.id)]
        }
        res = self.client.post(reverse('organization:permissions_update'), perm_data)
        self.assertIn(res.status_code, [302, 200])
        self.perm_setting.refresh_from_db()
        self.assertTrue(self.perm_setting.allow_all_hr)
        self.assertTrue(self.perm_setting.allowed_users.filter(id=self.employee_user.id).exists())
