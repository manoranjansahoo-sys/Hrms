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

    def test_hr_role_choices_restricted(self):
        # HR user form has only Employee and Site Manager
        form = EmployeeCreateForm(user=self.hr_user)
        role_choices = [c[0] for c in form.fields['role'].choices]
        self.assertIn(CustomUser.Role.EMPLOYEE, role_choices)
        self.assertIn(CustomUser.Role.SITE_MANAGER, role_choices)
        self.assertNotIn(CustomUser.Role.HR, role_choices)
        self.assertNotIn(CustomUser.Role.HEAD, role_choices)

    def test_admin_role_choices_unrestricted(self):
        admin_user = CustomUser.objects.create_superuser(
            username='super_admin',
            email='admin@example.com',
            role=CustomUser.Role.HEAD,
            password='AdminPassword123'
        )
        form = EmployeeCreateForm(user=admin_user)
        role_choices = [c[0] for c in form.fields['role'].choices]
        self.assertIn(CustomUser.Role.EMPLOYEE, role_choices)
        self.assertIn(CustomUser.Role.SITE_MANAGER, role_choices)
        self.assertIn(CustomUser.Role.HR, role_choices)
        self.assertIn(CustomUser.Role.HEAD, role_choices)

    def test_hr_cannot_create_hr_or_head_role(self):
        self.client.force_login(self.hr_user)
        post_data = {
            'first_name': 'Sneha',
            'last_name': 'Patil',
            'username': 'sneha_patil',
            'email': 'sneha.patil@company.com',
            'phone': '9876543219',
            'password': 'CustomSecret2026!',
            'confirm_password': 'CustomSecret2026!',
            'role': CustomUser.Role.HEAD,  # HR attempts to create HEAD
            'department': self.dept.id,
            'designation': self.desig.id,
            'site': self.site.id,
            'employment_type': 'FULL_TIME',
            'joining_date': '2026-11-04',
            'date_of_birth': '1996-08-20',
            'gender': 'FEMALE',
            'marital_status': 'SINGLE',
            'emergency_contact_phone': '8876543219',
            'bank_name': 'HDFC Bank',
            'bank_account_number': '987654321099',
            'ifsc_code': 'HDFC0001234',
            'pan_number': 'ABCDE9877Z',
        }
        res = self.client.post(reverse('employees:employee_create'), data=post_data)
        self.assertEqual(res.status_code, 200)
        form = res.context['form']
        self.assertIn('role', form.errors)

    def test_profile_correction_request_and_hr_approval_applies_bank_and_phone(self):
        # 1. Create an employee
        emp_user = CustomUser.objects.create_user(
            username='worker_one',
            email='worker1@company.com',
            phone='9111111111',
            password='PassWord123!'
        )
        emp_profile = EmployeeProfile.objects.create(
            user=emp_user,
            emp_id='EMP991',
            department=self.dept,
            designation=self.desig,
            site=self.site,
            joining_date=date(2026, 1, 1),
            bank_name='Old Bank',
            bank_account_number='111122223333',
            ifsc_code='OLDB0001234',
            pan_number='OLDPA1234F',
            emergency_contact_phone='9876543210'
        )

        # 2. Employee submits correction request for Bank Account Number
        self.client.force_login(emp_user)
        post_res = self.client.post(reverse('employees:profile_correction_request'), {
            'field_select': 'Bank Account Number',
            'field_name': 'Bank Account Number',
            'current_value': '111122223333',
            'proposed_value': '999988887777',
            'reason': 'Salary account changed to primary savings'
        }, follow=True)
        self.assertEqual(post_res.status_code, 200)

        # Verify request exists in DB
        from employees.models import ProfileCorrectionRequest
        req = ProfileCorrectionRequest.objects.filter(employee=emp_profile, field_name='Bank Account Number').first()
        self.assertIsNotNone(req)
        self.assertEqual(req.status, 'PENDING')
        self.assertEqual(req.proposed_value, '999988887777')

        # 3. HR approves the request
        self.client.force_login(self.hr_user)
        review_res = self.client.post(reverse('employees:review_profile_correction', kwargs={'request_id': req.id}), {
            'action': 'APPROVE',
            'notes': 'Verified with cancelled cheque'
        }, follow=True)
        self.assertEqual(review_res.status_code, 200)

        # Refresh employee profile from DB
        emp_profile.refresh_from_db()
        self.assertEqual(emp_profile.bank_account_number, '999988887777')
        req.refresh_from_db()
        self.assertEqual(req.status, 'APPROVED')
        self.assertEqual(req.reviewed_by, self.hr_user)

        # 4. Now test Mobile Phone update
        self.client.force_login(emp_user)
        post_phone = self.client.post(reverse('employees:profile_correction_request'), {
            'field_select': 'Mobile Phone Number',
            'field_name': 'Mobile Phone Number',
            'current_value': '9111111111',
            'proposed_value': '9222222222',
            'reason': 'Lost old SIM, activated new connection'
        }, follow=True)
        self.assertEqual(post_phone.status_code, 200)

        phone_req = ProfileCorrectionRequest.objects.filter(employee=emp_profile, field_name='Mobile Phone Number').first()
        self.assertIsNotNone(phone_req)

        # HR approves phone update
        self.client.force_login(self.hr_user)
        review_phone = self.client.post(reverse('employees:review_profile_correction', kwargs={'request_id': phone_req.id}), {
            'action': 'APPROVE',
            'notes': 'Verified OTP'
        }, follow=True)
        self.assertEqual(review_phone.status_code, 200)

        emp_user.refresh_from_db()
        self.assertEqual(emp_user.phone, '9222222222')
        phone_req.refresh_from_db()
        self.assertEqual(phone_req.status, 'APPROVED')

        # 5. Verify the employee profile detail page shows the updated values and approved request badge
        self.client.force_login(emp_user)
        detail_res = self.client.get(reverse('employees:employee_detail', kwargs={'emp_id': emp_profile.emp_id}))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, '999988887777')
        self.assertContains(detail_res, '9222222222')
        self.assertContains(detail_res, 'Approved & Applied')


class EmployeeDirectoryListAndPaginationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Engineering', code='ENG')
        self.site = Site.objects.create(name='Tech Campus', code='TC-1', city='Hyderabad')
        self.hr = CustomUser.objects.create_user(
            username='hr_admin_dir',
            email='hr_dir@example.com',
            role=CustomUser.Role.HR,
            password='AdminPassword123'
        )

        # Create 12 employees to test pagination (5, 10, 20)
        for i in range(1, 13):
            u = CustomUser.objects.create_user(
                username=f'worker_{i}',
                first_name=f'User{i:02d}',
                last_name=f'LastName{i:02d}',
                email=f'worker{i}@test.com',
                phone=f'98765432{i:02d}',
                role=CustomUser.Role.EMPLOYEE,
                password='Password123'
            )
            EmployeeProfile.objects.create(
                user=u,
                emp_id=f'EMP{1000 + i}',
                department=self.dept,
                site=self.site,
                joining_date=date(2026, 1, 1),
                status=EmployeeProfile.Status.ACTIVE if i % 2 == 0 else EmployeeProfile.Status.ON_NOTICE
            )

    def test_directory_default_pagination(self):
        self.client.force_login(self.hr)
        res = self.client.get(reverse('employees:employee_list'))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['page_obj']), 10)  # default 10 per page
        self.assertEqual(res.context['total_employees'], 12)
        self.assertContains(res, 'entries per page')
        self.assertNotContains(res, '<button type="submit" class="btn btn-sm btn-hrms w-100">Filter</button>')

    def test_directory_per_page_options(self):
        self.client.force_login(self.hr)
        # Request per_page=5
        res = self.client.get(reverse('employees:employee_list') + '?per_page=5')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.context['page_obj']), 5)
        self.assertEqual(res.context['selected_per_page'], 5)

        # Request per_page=20
        res20 = self.client.get(reverse('employees:employee_list') + '?per_page=20')
        self.assertEqual(res20.status_code, 200)
        self.assertEqual(len(res20.context['page_obj']), 12)
        self.assertEqual(res20.context['selected_per_page'], 20)

    def test_directory_status_filter_and_sort(self):
        self.client.force_login(self.hr)
        # Filter status ACTIVE
        res = self.client.get(reverse('employees:employee_list') + '?status=ACTIVE')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['page_obj'].paginator.count, 6)

        # Sort name ascending
        res_sort = self.client.get(reverse('employees:employee_list') + '?sort=name_asc')
        self.assertEqual(res_sort.status_code, 200)
        first_emp = res_sort.context['page_obj'][0]
        self.assertEqual(first_emp.user.first_name, 'User01')

