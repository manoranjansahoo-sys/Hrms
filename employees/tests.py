from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from organization.models import Department, Designation, Site
from employees.models import EmployeeProfile
from employees.forms import EmployeeCreateForm
from datetime import date


class EmployeeOnboardingAndLoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Technology', code='TECH')
        self.desig = Designation.objects.create(title='Backend Developer', department=self.dept)
        self.site = Site.objects.create(name='Bengaluru Campus', code='BLR-1', city='Bengaluru')

        # HR Admin
        self.hr_user = CustomUser.objects.create_user(
            username='hr_tester',
            email='hr_tester@example.com',
            role=CustomUser.Role.HR,
            password='TestPassword123'
        )

    def test_employee_form_valid(self):
        form_data = {
            'first_name': 'Aarav',
            'last_name': 'Sharma',
            'username': 'aarav_sharma',
            'email': 'aarav.sharma@example.com',
            'phone': '9876543210',
            'password': 'SecurePassword@123',
            'confirm_password': 'SecurePassword@123',
            'role': CustomUser.Role.EMPLOYEE,
            'department': self.dept.id,
            'designation': self.desig.id,
            'site': self.site.id,
            'employment_type': 'FULL_TIME',
            'joining_date': '2026-11-01',
            'date_of_birth': '1998-05-15',
            'gender': 'MALE',
            'marital_status': 'SINGLE',
            'emergency_contact_phone': '9876543211',
            'bank_name': 'HDFC Bank',
            'bank_account_number': '123456789012',
            'ifsc_code': 'HDFC0001234',
            'pan_number': 'ABCDE1234F',
            'uan_number': '',  # Optional
        }
        form = EmployeeCreateForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_employee_form_password_mismatch(self):
        form_data = {
            'first_name': 'Aarav',
            'last_name': 'Sharma',
            'username': 'aarav_sharma',
            'email': 'aarav.sharma@example.com',
            'phone': '9876543210',
            'password': 'SecurePassword@123',
            'confirm_password': 'DifferentPassword@123',
            'role': CustomUser.Role.EMPLOYEE,
            'department': self.dept.id,
            'designation': self.desig.id,
            'site': self.site.id,
            'employment_type': 'FULL_TIME',
            'joining_date': '2026-11-01',
            'date_of_birth': '1998-05-15',
            'gender': 'MALE',
            'marital_status': 'SINGLE',
            'emergency_contact_phone': '9876543211',
            'bank_name': 'HDFC Bank',
            'bank_account_number': '123456789012',
            'ifsc_code': 'HDFC0001234',
            'pan_number': 'ABCDE1234F',
        }
        form = EmployeeCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_password', form.errors)

    def test_employee_form_invalid_phone(self):
        # Phone starting with 3 or containing letters
        form_data = {
            'first_name': 'Aarav',
            'last_name': 'Sharma',
            'username': 'aarav_sharma',
            'email': 'aarav.sharma@example.com',
            'phone': '3876543210',  # Invalid start digit for primary phone
            'password': 'SecurePassword@123',
            'confirm_password': 'SecurePassword@123',
            'role': CustomUser.Role.EMPLOYEE,
            'department': self.dept.id,
            'designation': self.desig.id,
            'site': self.site.id,
            'employment_type': 'FULL_TIME',
            'joining_date': '2026-11-01',
            'date_of_birth': '1998-05-15',
            'gender': 'MALE',
            'marital_status': 'SINGLE',
            'emergency_contact_phone': '9876543211',
            'bank_name': 'HDFC Bank',
            'bank_account_number': '123456789012',
            'ifsc_code': 'HDFC0001234',
            'pan_number': 'ABCDE1234F',
        }
        form = EmployeeCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)

    def test_employee_creation_and_login_by_username_email_and_phone(self):
        self.client.force_login(self.hr_user)
        post_data = {
            'first_name': 'Rahul',
            'last_name': 'Verma',
            'username': 'rahul_verma',
            'email': 'rahul.verma@company.com',
            'phone': '9876543210',
            'password': 'CustomSecret2026!',
            'confirm_password': 'CustomSecret2026!',
            'role': CustomUser.Role.EMPLOYEE,
            'department': self.dept.id,
            'designation': self.desig.id,
            'site': self.site.id,
            'employment_type': 'FULL_TIME',
            'joining_date': '2026-11-04',
            'date_of_birth': '1996-08-20',
            'gender': 'MALE',
            'marital_status': 'SINGLE',
            'emergency_contact_phone': '8876543210',
            'bank_name': 'State Bank of India',
            'bank_account_number': '987654321098',
            'ifsc_code': 'SBIN0001234',
            'pan_number': 'ABCDE9876Z',
            'uan_number': '101234567890',
        }

        response = self.client.post(reverse('employees:employee_create'), data=post_data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Verify user created
        new_user = CustomUser.objects.filter(username='rahul_verma').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.email, 'rahul.verma@company.com')
        self.assertEqual(new_user.phone, '9876543210')
        self.assertEqual(new_user.role, CustomUser.Role.EMPLOYEE)

        # Verify profile created with auto EMP ID
        profile = EmployeeProfile.objects.filter(user=new_user).first()
        self.assertIsNotNone(profile)
        self.assertTrue(profile.emp_id.startswith('EMP'))
        self.assertEqual(profile.uan_number, '101234567890')
        self.assertEqual(profile.pan_number, 'ABCDE9876Z')

        # Logout HR
        self.client.logout()

        # 1. Login as the new employee using USERNAME and password
        login_success = self.client.login(username='rahul_verma', password='CustomSecret2026!')
        self.assertTrue(login_success)

        # Access employee directory
        dir_res = self.client.get(reverse('employees:employee_list'))
        self.assertEqual(dir_res.status_code, 200)
        self.assertContains(dir_res, 'Rahul Verma')
        self.assertContains(dir_res, profile.emp_id)

        # Access employee detail (profile)
        profile_res = self.client.get(reverse('employees:employee_detail', kwargs={'emp_id': profile.emp_id}))
        self.assertEqual(profile_res.status_code, 200)
        self.assertContains(profile_res, 'Rahul Verma')

        # Logout
        self.client.logout()

        # 2. Login as the new employee using EMAIL and password via login post
        login_email_res = self.client.post(reverse('accounts:login'), {
            'username': 'rahul.verma@company.com',
            'password': 'CustomSecret2026!'
        }, follow=True)
        self.assertEqual(login_email_res.status_code, 200)
        self.assertTrue(login_email_res.context['user'].is_authenticated)
        self.assertEqual(login_email_res.context['user'].username, 'rahul_verma')

        # Logout
        self.client.logout()

        # 3. Login as the new employee using PHONE NUMBER and password via login post
        login_phone_res = self.client.post(reverse('accounts:login'), {
            'username': '9876543210',
            'password': 'CustomSecret2026!'
        }, follow=True)
        self.assertEqual(login_phone_res.status_code, 200)
        self.assertTrue(login_phone_res.context['user'].is_authenticated)
        self.assertEqual(login_phone_res.context['user'].username, 'rahul_verma')
