import tempfile
from datetime import date, time, timedelta
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core import mail
from accounts.models import CustomUser
from organization.models import Department, Site
from recruitment.models import (
    RecruitmentJob, CandidateRegistrationLink, Candidate,
    CandidateEducation, CandidateExperience, CandidateSkill,
    CandidateDocument, JobApplication, ApplicationStatusHistory
)


@override_settings(MEDIA_ROOT=tempfile.gettempdir())
class RecruitmentTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Users with different roles
        self.hr_user = CustomUser.objects.create_user(
            username='test_hr',
            email='test_hr@company.com',
            password='password123',
            role='hr',
            first_name='Pooja',
            last_name='Menon'
        )
        self.emp_user = CustomUser.objects.create_user(
            username='test_emp',
            email='test_emp@company.com',
            password='password123',
            role='employee',
            first_name='John',
            last_name='Doe'
        )
        self.mgr_user = CustomUser.objects.create_user(
            username='test_mgr',
            email='test_mgr@company.com',
            password='password123',
            role='site_manager',
            first_name='Rajesh',
            last_name='Verma'
        )
        self.head_user = CustomUser.objects.create_user(
            username='test_head',
            email='test_head@company.com',
            password='password123',
            role='head',
            first_name='Vikramaditya',
            last_name='Singhania'
        )

        # Department & Site
        self.dept = Department.objects.create(name='Engineering', code='ENG')
        self.site = Site.objects.create(name='Bengaluru HQ', code='BLR-HQ', city='Bengaluru')

        # Job Opening
        self.job = RecruitmentJob.objects.create(
            title='Senior Backend Engineer',
            department=self.dept,
            site=self.site,
            location='Bengaluru & Hybrid',
            employment_type=RecruitmentJob.EmploymentType.FULL_TIME,
            vacancies=2,
            experience_required='4-7 Years',
            salary_range='₹18,00,000 - ₹25,00,000 PA',
            description='Build scalable enterprise microservices.',
            requirements='Python, Django, PostgreSQL, Docker.',
            application_deadline=timezone.localdate() + timedelta(days=30),
            status=RecruitmentJob.Status.OPEN,
            created_by=self.hr_user
        )

        # Candidate Registration Link
        self.link = CandidateRegistrationLink.objects.create(
            job=self.job,
            title='Tech Sourcing Campaign',
            expires_at=timezone.now() + timedelta(days=20),
            max_applications=50,
            is_active=True,
            created_by=self.hr_user
        )

    def test_token_auto_generation(self):
        """Link automatically receives a unique non-empty URL-safe token."""
        self.assertTrue(self.link.token)
        self.assertGreater(len(self.link.token), 10)
        self.assertTrue(self.link.is_valid)
        self.assertEqual(self.link.status_label, 'Active')

    def test_link_expiration_and_limit_properties(self):
        """Expired and max-application reached links are marked invalid."""
        expired_link = CandidateRegistrationLink.objects.create(
            job=self.job,
            title='Expired Link Test',
            expires_at=timezone.now() - timedelta(days=1),
            is_active=True
        )
        self.assertTrue(expired_link.is_expired)
        self.assertFalse(expired_link.is_valid)
        self.assertEqual(expired_link.status_label, 'Expired')

        inactive_link = CandidateRegistrationLink.objects.create(
            job=self.job,
            title='Deactivated Link Test',
            is_active=False
        )
        self.assertFalse(inactive_link.is_valid)
        self.assertEqual(inactive_link.status_label, 'Closed')

    def test_rbac_hr_management_pages(self):
        """Only HR and Head can access recruitment management; Employees and Site Managers get 403."""
        links_url = reverse('recruitment:links_list')

        # Anonymous redirected to login
        resp = self.client.get(links_url)
        self.assertEqual(resp.status_code, 302)

        # Employee gets 403 Forbidden
        self.client.login(username='test_emp', password='password123')
        resp = self.client.get(links_url)
        self.assertEqual(resp.status_code, 403)
        self.client.logout()

        # Site Manager gets 403 Forbidden
        self.client.login(username='test_mgr', password='password123')
        resp = self.client.get(links_url)
        self.assertEqual(resp.status_code, 403)
        self.client.logout()

        # HR Admin gets 200 OK
        self.client.login(username='test_hr', password='password123')
        resp = self.client.get(links_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Candidate Registration Portal & Positions')
        self.client.logout()

        # Head / Super Admin gets 200 OK
        self.client.login(username='test_head', password='password123')
        resp = self.client.get(links_url)
        self.assertEqual(resp.status_code, 200)

    def test_public_pre_interview_registration_page_view(self):
        """Public pre-interview registration page loads with required fields."""
        reg_url = reverse('recruitment:candidate_register', kwargs={'token': self.link.token})
        resp = self.client.get(reg_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Senior Backend Engineer')
        self.assertContains(resp, 'Candidate Registration & Job Application')
        self.assertContains(resp, 'Current Residential Address')
        self.assertContains(resp, 'Submit Application')

    def test_public_registration_expired_link(self):
        """Accessing expired or closed link renders link_invalid template."""
        self.link.is_active = False
        self.link.save()

        reg_url = reverse('recruitment:candidate_register', kwargs={'token': self.link.token})
        resp = self.client.get(reg_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Registration Link No Longer Active')

    def test_pre_interview_registration_submission(self):
        """Candidate submits streamlined 1-page form: verifies quick submission and resume upload."""
        reg_url = reverse('recruitment:candidate_register', kwargs={'token': self.link.token})
        dummy_resume = SimpleUploadedFile(
            "ananya_backend_cv.pdf",
            b"%PDF-1.4 Mock CV Content for testing",
            content_type="application/pdf"
        )

        form_data = {
            'full_name': 'Ananya Sengupta',
            'email': 'ananya.sengupta@example.com',
            'phone': '+91 91234 56789',
            'alt_phone': '+91 91234 56780',
            'current_address': 'Flat 201, Maple Heights, HSR Layout',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'postal_code': '560102',
            'country': 'India',
            'highest_qualification': 'B.Tech in Information Technology',
            'institution': 'IIT Kharagpur',
            'experience_type': 'EXPERIENCED',
            'total_experience_years': '4',
            'current_company': 'Tech Corp',
            'current_designation': 'Software Engineer',
            'notice_period_days': '30',
            'expected_ctc': '2000000',
            'technical_skills': 'Python, Django, PostgreSQL, Docker, Redis',
            'resume': dummy_resume,
            'portfolio_url': 'https://ananya.dev',
            'linkedin_url': 'https://linkedin.com/in/ananya-sample',
        }

        resp = self.client.post(reg_url, form_data)
        self.assertEqual(resp.status_code, 302)

        # Check candidate & application created
        candidate = Candidate.objects.filter(email='ananya.sengupta@example.com').first()
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate.full_name, 'Ananya Sengupta')
        self.assertEqual(candidate.alt_phone, '+91 91234 56780')
        self.assertEqual(candidate.current_address, 'Flat 201, Maple Heights, HSR Layout')
        self.assertEqual(candidate.city, 'Bengaluru')
        self.assertEqual(candidate.state, 'Karnataka')
        self.assertEqual(candidate.postal_code, '560102')
        self.assertEqual(candidate.country, 'India')
        self.assertEqual(candidate.education.highest_qualification, 'B.Tech in Information Technology')
        self.assertEqual(candidate.experience.total_experience_years, 4)
        self.assertIn('Django', candidate.skills.technical_skills)

        application = JobApplication.objects.filter(candidate=candidate, job=self.job).first()
        self.assertIsNotNone(application)
        self.assertTrue(application.application_id.startswith('APP-') or application.application_id.startswith('HRMS-'))
        self.assertEqual(application.status, JobApplication.Status.SUBMITTED)
        self.assertFalse(application.is_onboarding_completed)

        # Verify redirect to success page
        success_url = reverse('recruitment:candidate_success', kwargs={'application_id': application.application_id})
        self.assertRedirects(resp, success_url)

        # Verify confirmation email sent
        self.assertGreater(len(mail.outbox), 0)
        self.assertIn('Application Received', mail.outbox[0].subject)
        self.assertIn(application.application_id, mail.outbox[0].body)

        # Check tracking page displays application status
        track_url = reverse('recruitment:candidate_track_id', kwargs={'application_id': application.application_id})
        track_resp = self.client.get(track_url)
        self.assertEqual(track_resp.status_code, 200)
        self.assertContains(track_resp, application.application_id)
        self.assertContains(track_resp, 'Submitted')

    def test_hr_interview_scheduling_and_qualification(self):
        """HR schedules interview and marks candidate as qualified/selected."""
        dummy_resume = SimpleUploadedFile("cv.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        candidate = Candidate.objects.create(
            full_name='Vikram Sethi',
            email='vikram.sethi@example.com',
            phone='+91 99999 88888',
            city='Bengaluru',
            country='India'
        )
        app = JobApplication.objects.create(
            candidate=candidate,
            job=self.job,
            registration_link=self.link,
            resume=dummy_resume,
            status=JobApplication.Status.SUBMITTED
        )

        self.client.login(username='test_hr', password='password123')
        detail_url = reverse('recruitment:candidate_detail', kwargs={'application_id': app.id})

        # 1. Schedule interview
        interview_post = {
            'action_type': 'SCHEDULE_INTERVIEW',
            'interview_date': (timezone.localdate() + timedelta(days=2)).strftime('%Y-%m-%d'),
            'interview_time': '15:30',
            'interview_mode': 'VIRTUAL',
            'interview_location_link': 'https://meet.google.com/test-room-123',
            'interview_notes': 'Technical Architecture & System Design Discussion'
        }
        resp = self.client.post(detail_url, interview_post)
        self.assertEqual(resp.status_code, 302)

        app.refresh_from_db()
        self.assertEqual(app.status, JobApplication.Status.INTERVIEW_SCHEDULED)

        # 2. Candidate clears interview: HR marks candidate as SELECTED (Qualified)
        review_post = {
            'action_type': 'UPDATE_REVIEW',
            'status': JobApplication.Status.SELECTED,
            'rating': 5,
            'hr_notes': 'Candidate cleared technical and managerial rounds with distinction.'
        }
        resp2 = self.client.post(detail_url, review_post)
        self.assertEqual(resp2.status_code, 302)

        app.refresh_from_db()
        self.assertEqual(app.status, JobApplication.Status.SELECTED)
        self.assertTrue(app.is_qualified)

    def test_post_interview_onboarding_workflow(self):
        """Once candidate qualifies in interview, full onboarding form unlocks and captures complete details."""
        dummy_resume = SimpleUploadedFile("cv.pdf", b"%PDF-1.4 test", content_type="application/pdf")
        candidate = Candidate.objects.create(
            full_name='Sneha Reddy',
            email='sneha.reddy@example.com',
            phone='+91 98888 77777',
            city='Hyderabad',
            country='India'
        )
        CandidateEducation.objects.create(
            candidate=candidate,
            highest_qualification='B.Tech in Computer Science'
        )
        app = JobApplication.objects.create(
            candidate=candidate,
            job=self.job,
            registration_link=self.link,
            resume=dummy_resume,
            status=JobApplication.Status.SUBMITTED
        )

        onboarding_url = reverse('recruitment:candidate_onboarding', kwargs={'application_id': app.application_id})

        # Before interview qualification: Onboarding form shows "Interview in Progress"
        resp1 = self.client.get(onboarding_url)
        self.assertContains(resp1, 'Interview In Progress')

        # Qualify candidate in interview
        app.status = JobApplication.Status.SELECTED
        app.save()

        # After qualification: Onboarding form opens cleanly
        resp2 = self.client.get(onboarding_url)
        self.assertEqual(resp2.status_code, 200)
        self.assertContains(resp2, 'Official Employee Onboarding Portal')
        self.assertContains(resp2, 'Salary Bank Details')
        # Section 5 Create Portal Credentials removed from candidate onboarding form
        self.assertNotContains(resp2, '5. Create HRMS Portal Login Credentials')
        self.assertNotContains(resp2, 'chinmayee_mohanty_ux')

        # Candidate submits full onboarding details with documents and statutory PF UAN (No login credentials)
        dummy_cert = SimpleUploadedFile("degree.pdf", b"%PDF-1.4 Degree Cert", content_type="application/pdf")
        onboarding_post_data = {
            'date_of_birth': '1997-06-25',
            'gender': 'FEMALE',
            'father_name': 'K. V. Reddy',
            'blood_group': 'B+',
            'marital_status': 'SINGLE',
            'emergency_contact_name': 'K. V. Reddy',
            'emergency_contact_relation': 'Father',
            'emergency_contact_phone': '9888800000',
            'current_address': 'Flat 302, Cyber Towers Area, Hitech City',
            'permanent_address': 'Plot 45, Srinagar Colony, Hyderabad',
            'state': 'Telangana',
            'postal_code': '500081',
            'degree_name': 'Bachelor of Technology in Computer Science',
            'specialization': 'Computer Science',
            'institution': 'JNTU Hyderabad',
            'passing_year': '2019',
            'percentage_cgpa': '8.6 CGPA',
            'details_10th': 'State Board 2013 - 92%',
            'details_12th': 'Inter Board 2015 - 94%',
            'educational_certificate': dummy_cert,
            'bank_name': 'HDFC Bank',
            'bank_account_number': '50100234567890',
            'bank_ifsc_code': 'HDFC0000123',
            'bank_branch': 'Hitech City Branch',
            'pan_number': 'ABCDE1234F',
            'aadhaar_number': '987654321098',
            'pf_uan_number': '101234567890',
            'accuracy_declaration': 'on',
        }

        resp3 = self.client.post(onboarding_url, onboarding_post_data)
        self.assertEqual(resp3.status_code, 200)
        self.assertContains(resp3, 'Onboarding Documents Submitted Successfully!')
        self.assertContains(resp3, 'Pending HR Document Verification & Appointment')

        app.refresh_from_db()
        candidate.refresh_from_db()
        self.assertTrue(app.is_onboarding_completed)
        self.assertEqual(app.status, JobApplication.Status.ONBOARDING_COMPLETED)
        self.assertEqual(app.document_verification_status, JobApplication.DocumentVerificationStatus.PENDING)
        self.assertEqual(candidate.father_name, 'K. V. Reddy')
        self.assertEqual(candidate.bank_name, 'HDFC Bank')
        self.assertEqual(candidate.pan_number, 'ABCDE1234F')
        self.assertEqual(candidate.pf_uan_number, '101234567890')

        # -------------------------------------------------------------
        # STEP 2: HR Document Verification & Error Handling
        # -------------------------------------------------------------
        self.client.login(username='test_hr', password='password123')

        # HR views onboarding candidates list
        onboarding_list_url = reverse('recruitment:onboarding_candidates_list')
        list_resp = self.client.get(onboarding_list_url)
        self.assertEqual(list_resp.status_code, 200)
        self.assertContains(list_resp, 'Sneha Reddy')
        self.assertContains(list_resp, 'Pending Review')

        # Scenario A: HR finds documentation error and rejects documents with feedback
        reject_url = reverse('recruitment:verify_candidate_documents', kwargs={'application_id': app.application_id})
        reject_resp = self.client.post(reject_url, {
            'action': 'REJECT',
            'rejection_reason': 'Degree certificate is blurry. Please re-upload clear marksheet.'
        })
        self.assertEqual(reject_resp.status_code, 302)
        app.refresh_from_db()
        self.assertEqual(app.document_verification_status, JobApplication.DocumentVerificationStatus.REJECTED)
        self.assertEqual(app.document_rejection_reason, 'Degree certificate is blurry. Please re-upload clear marksheet.')

        # Candidate opens onboarding link and sees the rejection error alert
        cand_reopen_resp = self.client.get(onboarding_url)
        self.assertEqual(cand_reopen_resp.status_code, 200)
        self.assertContains(cand_reopen_resp, 'Documentation Error — Re-upload / Correction Requested')
        self.assertContains(cand_reopen_resp, 'Degree certificate is blurry. Please re-upload clear marksheet.')

        # Scenario B: HR reviews re-uploaded documents and marks as VERIFIED
        verify_resp = self.client.post(reject_url, {'action': 'VERIFY'})
        self.assertEqual(verify_resp.status_code, 302)
        app.refresh_from_db()
        self.assertEqual(app.document_verification_status, JobApplication.DocumentVerificationStatus.VERIFIED)

        # -------------------------------------------------------------
        # STEP 3: Auto-Fetch Candidate by Phone or Email AJAX Endpoint
        # -------------------------------------------------------------
        fetch_url = reverse('recruitment:fetch_onboarding_candidate_ajax')
        # Fetch by phone
        fetch_resp_phone = self.client.get(f"{fetch_url}?q=9888877777")
        self.assertEqual(fetch_resp_phone.status_code, 200)
        phone_data = fetch_resp_phone.json()
        self.assertTrue(phone_data['success'])
        self.assertEqual(phone_data['candidate']['full_name'], 'Sneha Reddy')
        self.assertEqual(phone_data['candidate']['document_status'], 'VERIFIED')
        self.assertTrue(phone_data['candidate']['suggested_username'].startswith('sneha_reddy'))

        # Fetch by email
        fetch_resp_email = self.client.get(f"{fetch_url}?q=sneha.reddy@example.com")
        self.assertEqual(fetch_resp_email.status_code, 200)
        email_data = fetch_resp_email.json()
        self.assertTrue(email_data['success'])
        self.assertEqual(email_data['candidate']['full_name'], 'Sneha Reddy')

        # -------------------------------------------------------------
        # STEP 4: HR Appoints Candidate as Official Employee
        # -------------------------------------------------------------
        appoint_url = reverse('recruitment:appoint_employee')

        # GET page loads cleanly with prefill or form
        appoint_get = self.client.get(f"{appoint_url}?app_id={app.application_id}")
        self.assertEqual(appoint_get.status_code, 200)
        self.assertContains(appoint_get, 'Candidate Identification & Profile Lookup')
        self.assertContains(appoint_get, 'Create Official HRMS Portal Login Credentials')

        # HR submits appointment with official username and password
        appoint_post_data = {
            'lookup_query': 'sneha.reddy@example.com',
            'application_id': app.application_id,
            'candidate_id': str(candidate.id),
            'department': self.dept.id,
            'designation_title': 'Senior Backend Engineer',
            'site': self.site.id,
            'joining_date': '2026-11-15',
            'employment_type': 'FULL_TIME',
            'offered_ctc': '720000.00',
            'basic_salary': '30000.00',
            'username': 'sneha_reddy',
            'password': 'MyPassword@123',
            'confirm_password': 'MyPassword@123',
            'confirm_appointment': 'on',
        }
        appoint_post_resp = self.client.post(appoint_url, appoint_post_data)
        self.assertEqual(appoint_post_resp.status_code, 302)

        app.refresh_from_db()
        self.assertEqual(app.status, JobApplication.Status.HIRED)
        self.assertIsNotNone(app.hired_employee)

        # Verify CustomUser was created with the specified credentials
        created_employee_user = CustomUser.objects.filter(email='sneha.reddy@example.com').first()
        self.assertIsNotNone(created_employee_user)
        self.assertEqual(created_employee_user.role, CustomUser.Role.EMPLOYEE)
        self.assertEqual(created_employee_user.username, 'sneha_reddy')

        # Verify Employee Profile created
        self.assertEqual(created_employee_user.employee_profile.department, self.dept)
        self.assertEqual(str(created_employee_user.employee_profile.joining_date), '2026-11-15')

        # Verify Payroll Salary Structure created
        from payroll.models import SalaryStructure
        sal_struct = SalaryStructure.objects.filter(employee=created_employee_user.employee_profile).first()
        self.assertIsNotNone(sal_struct)
        self.assertEqual(sal_struct.basic_salary, 30000.00)

        # Employee logs into HRMS with their new HR-created credentials
        self.client.logout()
        login_ok = self.client.login(username='sneha_reddy', password='MyPassword@123')
        self.assertTrue(login_ok)

        # Employee logs in with their new credentials and views profile
        login_ok = self.client.login(username='sneha_reddy', password='MyPassword@123')
        self.assertTrue(login_ok)
        profile_resp = self.client.get(reverse('employees:employee_detail', kwargs={'emp_id': created_employee_user.employee_profile.emp_id}))
        self.assertEqual(profile_resp.status_code, 200)
        self.assertContains(profile_resp, 'Sneha Reddy')
        self.assertContains(profile_resp, 'HDFC0000123')

        # Also verify candidate detail page displays active employee profile for HR
        self.client.login(username='test_hr', password='password123')
        hr_detail_resp = self.client.get(reverse('recruitment:candidate_detail', kwargs={'application_id': app.id}))
        self.assertEqual(hr_detail_resp.status_code, 200)
        self.assertContains(hr_detail_resp, created_employee_user.employee_profile.emp_id)
        self.assertContains(hr_detail_resp, 'Open Profile')

    def test_universal_candidate_application_master_link(self):
        """Universal application master link loads open positions and accepts submissions."""
        # Create second job opening in master data
        job2 = RecruitmentJob.objects.create(
            title='Frontend UI/UX Specialist',
            department=self.dept,
            site=self.site,
            location='Remote / Hybrid',
            employment_type=RecruitmentJob.EmploymentType.FULL_TIME,
            vacancies=3,
            experience_required='2-4 Years',
            description='Design and build responsive enterprise UIs.',
            requirements='React, Bootstrap, JavaScript, Figma.',
            status=RecruitmentJob.Status.OPEN,
            created_by=self.hr_user
        )

        apply_url = reverse('recruitment:candidate_apply')
        resp = self.client.get(apply_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Senior Backend Engineer')
        self.assertContains(resp, 'Frontend UI/UX Specialist')
        self.assertContains(resp, 'Position / Job Role You Are Applying For')

        dummy_resume = SimpleUploadedFile(
            "candidate_cv.pdf",
            b"%PDF-1.4 Mock CV Content",
            content_type="application/pdf"
        )
        post_data = {
            'job': job2.id,
            'full_name': 'Karan Mehra',
            'email': 'karan.mehra@example.com',
            'phone': '+91 98888 77777',
            'current_address': 'Flat 12, Ocean View, Bandra West',
            'city': 'Mumbai',
            'state': 'Maharashtra',
            'postal_code': '400050',
            'country': 'India',
            'highest_qualification': 'MCA (Master of Computer Applications)',
            'institution': 'Mumbai University',
            'experience_type': 'EXPERIENCED',
            'total_experience_years': '3',
            'current_company': 'Innovatech',
            'current_designation': 'Frontend Developer',
            'notice_period_days': '15',
            'expected_ctc': '1400000',
            'technical_skills': 'React, JavaScript, CSS, HTML5',
            'resume': dummy_resume,
        }

        resp_post = self.client.post(apply_url, post_data)
        self.assertEqual(resp_post.status_code, 302)

        app = JobApplication.objects.filter(candidate__email='karan.mehra@example.com', job=job2).first()
        self.assertIsNotNone(app)
        self.assertEqual(app.job.title, 'Frontend UI/UX Specialist')
        self.assertTrue(app.application_id.startswith('APP-'))
        self.assertEqual(app.status, JobApplication.Status.SUBMITTED)

    def test_candidate_fast_apply_page_and_submission(self):
        """Test the LinkedIn & Website direct fast-apply portal with Google auth and contact fields."""
        fast_apply_url = reverse('recruitment:candidate_fast_apply')

        # 1. GET page
        resp_get = self.client.get(fast_apply_url)
        self.assertEqual(resp_get.status_code, 200)
        self.assertContains(resp_get, 'Sign up with Google')
        self.assertNotContains(resp_get, '<span>Sign in with Google</span>')
        self.assertContains(resp_get, 'Alternative Phone Number')
        self.assertNotContains(resp_get, 'Current Residential Address')
        self.assertContains(resp_get, 'Clear form')
        self.assertNotContains(resp_get, 'Quick Application • LinkedIn & Website Fast Portal')
        self.assertNotContains(resp_get, 'Equal Opportunity Employer')

        # 2. POST submission
        dummy_resume = SimpleUploadedFile(
            "aarav_resume.pdf",
            b"%PDF-1.4 Fast apply CV content",
            content_type="application/pdf"
        )
        post_data = {
            'job': self.job.id,
            'full_name': 'Aarav Patel',
            'email': 'aarav.patel@gmail.com',
            'phone': '+91 98765 43210',
            'alt_phone': '+91 98765 43211',
            'resume': dummy_resume,
        }
        resp_post = self.client.post(fast_apply_url, post_data)
        self.assertEqual(resp_post.status_code, 302)

        # 3. Verify Candidate created with alt_phone
        cand = Candidate.objects.filter(email='aarav.patel@gmail.com').first()
        self.assertIsNotNone(cand)
        self.assertEqual(cand.full_name, 'Aarav Patel')
        self.assertEqual(cand.phone, '+91 98765 43210')
        self.assertEqual(cand.alt_phone, '+91 98765 43211')

        # 4. Verify JobApplication created as online fast-apply
        app = JobApplication.objects.filter(candidate=cand, job=self.job).first()
        self.assertIsNotNone(app)
        self.assertEqual(app.status, JobApplication.Status.SUBMITTED)
        self.assertFalse(app.is_office_registered)
        self.assertEqual(app.application_type, JobApplication.ApplicationType.ONLINE_FAST_APPLY)

        # 4b. Candidate arrives at office and completes in-person registration (Form 2)
        reg_url = reverse('recruitment:candidate_register', kwargs={'token': self.link.token})
        office_post_data = {
            'job': self.job.id,
            'full_name': 'Aarav Patel',
            'email': 'aarav.patel@gmail.com',
            'phone': '+91 98765 43210',
            'current_address': 'Flat 402, Sunrise Towers, Indiranagar',
            'city': 'Bengaluru',
            'state': 'Karnataka',
            'postal_code': '560038',
            'country': 'India',
            'highest_qualification': 'B.Tech / B.E.',
            'experience_type': 'EXPERIENCED',
            'technical_skills': 'Python, Django, AWS',
            'resume': SimpleUploadedFile('aarav_cv2.pdf', b'updated pdf bytes', content_type='application/pdf'),
        }
        resp_office = self.client.post(reg_url, office_post_data)
        self.assertEqual(resp_office.status_code, 302)
        app.refresh_from_db()
        self.assertTrue(app.is_office_registered)
        self.assertEqual(app.application_type, JobApplication.ApplicationType.OFFICE_REGISTRATION)
        cand.refresh_from_db()
        self.assertIn('Sunrise Towers', cand.current_address)

        # 5. Check links_list view includes fast-apply link and table pagination/search controls
        self.client.login(username='test_hr', password='password123')
        links_resp = self.client.get(reverse('recruitment:links_list'))
        self.assertEqual(links_resp.status_code, 200)
        self.assertContains(links_resp, 'fast-apply')
        self.assertContains(links_resp, 'jobSearchInput')
        self.assertContains(links_resp, 'pageSizeSelect')
        # Verify removed texts
        self.assertNotContains(links_resp, 'Positions currently available for applicant selection in the universal registration portal.')
        self.assertNotContains(links_resp, 'Total Positions')

        # 6. Check fast-apply with specific job id: role dropdown hidden, target role shown
        resp_job_fixed = self.client.get(f"{fast_apply_url}?job={self.job.id}")
        self.assertEqual(resp_job_fixed.status_code, 200)
        self.assertContains(resp_job_fixed, 'Target Position')
        self.assertNotContains(resp_job_fixed, '<select name="job"')

        # 7. Check fast-apply without job id: role dropdown visible
        resp_no_job = self.client.get(fast_apply_url)
        self.assertEqual(resp_no_job.status_code, 200)
        self.assertContains(resp_no_job, '<select name="job"')
        self.assertContains(links_resp, 'prevPageBtn')
        self.assertContains(links_resp, 'nextPageBtn')

    def test_candidates_list_six_columns(self):
        """Verify the candidate pipeline table has 6 clean columns, clickable rows, status icons, and no side bar drawer."""
        cand = Candidate.objects.create(
            full_name='Aarav Sharma',
            email='aarav.sharma@gmail.com',
            phone='+91 98765 43210'
        )
        app = JobApplication.objects.create(
            candidate=cand,
            job=self.job,
            status=JobApplication.Status.SUBMITTED
        )

        self.client.login(username='test_hr', password='password123')
        resp = self.client.get(reverse('recruitment:candidates_list'))
        self.assertEqual(resp.status_code, 200)

        # 1. Verify exact 6 column headers
        self.assertContains(resp, 'Application ID')
        self.assertContains(resp, 'Name')
        self.assertContains(resp, 'Email ID')
        self.assertContains(resp, 'Phone No')
        self.assertContains(resp, 'Position Name')
        self.assertContains(resp, 'Actions')

        # 2. Verify row content: Applied on DD/MM/YYYY subtext in ID column, candidate details
        today_formatted = timezone.localtime(app.applied_at).strftime('%d/%m/%Y')
        self.assertContains(resp, f'Applied on {today_formatted}')
        self.assertContains(resp, 'Aarav Sharma')
        self.assertContains(resp, 'aarav.sharma@gmail.com')
        self.assertContains(resp, '+91 98765 43210')

        # 3. Verify clickable row navigating to candidate detail
        self.assertContains(resp, 'clickable-candidate-row')
        self.assertContains(resp, reverse('recruitment:candidate_detail', kwargs={'application_id': app.id}))

        # 4. Verify clean status icon (clock history for submitted) and CV icon (no review button or boxes)
        self.assertContains(resp, 'status-icon-indicator')
        self.assertContains(resp, 'bi-clock-history')
        self.assertContains(resp, 'action-icon-cv')
        self.assertNotContains(resp, 'action-icon-review')
        self.assertNotContains(resp, 'btn-action-review')
        self.assertNotContains(resp, 'btn-action-pdf')

        # 5. Verify right-side side bar drawer is removed from candidate pipeline
        self.assertNotContains(resp, 'id="candidateDetailsOffcanvas"')

        # 6. Verify filter button is removed and dropdowns auto-submit on change
        self.assertNotContains(resp, '>Filter</button>')
        self.assertContains(resp, 'onchange="this.form.submit()"')

        # 7. Verify unified table footer with 5, 10, 20, 50, 100 page size and pagination
        self.assertContains(resp, 'pageSizeSelect')
        self.assertContains(resp, 'paginationControls')

    def test_google_auth_and_returning_candidate_autofill(self):
        """
        Verify real Google Sign-In authentication, session gating,
        automatic candidate identity recognition, database auto-population,
        and talent roster Google-verified badge display.
        """
        import json

        # 0. Verify button wording on Candidate Job Application vs Candidate Registration
        fast_apply_get = self.client.get(reverse('recruitment:candidate_fast_apply'))
        self.assertContains(fast_apply_get, 'Sign up with Google')
        self.assertNotContains(fast_apply_get, '<span>Sign in with Google</span>')

        register_get = self.client.get(reverse('recruitment:candidate_register', kwargs={'token': self.link.token}))
        self.assertContains(register_get, 'Log in with Google')
        self.assertNotContains(register_get, 'Sign up with Google')

        # 1. New Candidate authenticates via Google Auth API
        google_payload = {
            'email': 'priya.nair@gmail.com',
            'name': 'Priya Nair',
            'sub': 'google-oauth2-1029384756',
            'picture': 'https://lh3.googleusercontent.com/a/test-avatar'
        }
        auth_resp = self.client.post(
            reverse('recruitment:candidate_google_auth'),
            data=json.dumps(google_payload),
            content_type='application/json'
        )
        self.assertEqual(auth_resp.status_code, 200)
        auth_data = auth_resp.json()
        self.assertTrue(auth_data['success'])
        self.assertFalse(auth_data['is_returning_candidate'])
        self.assertEqual(auth_data['google_user']['email'], 'priya.nair@gmail.com')

        # 2. Candidate completes Fast Apply form
        resume_file = SimpleUploadedFile("priya_resume.pdf", b"%PDF-1.4 test resume bytes", content_type="application/pdf")
        apply_resp = self.client.post(
            reverse('recruitment:candidate_fast_apply_job', kwargs={'job_id': self.job.id}),
            data={
                'job': self.job.id,
                'full_name': 'Priya Nair',
                'email': 'priya.nair@gmail.com',
                'phone': '9876543210',
                'alt_phone': '9876543211',
                'resume': resume_file,
                'is_google_verified': 'true'
            }
        )
        # Should redirect to candidate success page
        self.assertEqual(apply_resp.status_code, 302)

        # Verify candidate created with Google Verified status
        candidate = Candidate.objects.get(email='priya.nair@gmail.com')
        self.assertTrue(candidate.is_google_verified)
        self.assertEqual(candidate.google_sub, 'google-oauth2-1029384756')
        self.assertEqual(candidate.city, self.job.location)

        # Add education and skills for this candidate
        CandidateEducation.objects.create(
            candidate=candidate,
            highest_qualification='M.Tech Computer Science',
            institution='IIT Kharagpur'
        )
        CandidateExperience.objects.create(
            candidate=candidate,
            experience_type='EXPERIENCED',
            total_experience_years=5,
            current_company='Tech Innovations Ltd',
            current_designation='Lead Software Architect'
        )
        CandidateSkill.objects.create(
            candidate=candidate,
            technical_skills='Python, Django, AWS, Kubernetes',
            linkedin_url='https://linkedin.com/in/priyanair'
        )

        # 3. Candidate later opens Registration link sent by HR
        # When logging in with the SAME Google account:
        re_auth_resp = self.client.post(
            reverse('recruitment:candidate_google_auth'),
            data=json.dumps(google_payload),
            content_type='application/json'
        )
        self.assertEqual(re_auth_resp.status_code, 200)
        re_auth_data = re_auth_resp.json()
        self.assertTrue(re_auth_data['success'])
        # MUST identify that same person!
        self.assertTrue(re_auth_data['is_returning_candidate'])
        self.assertIsNotNone(re_auth_data['candidate_data'])
        c_data = re_auth_data['candidate_data']
        self.assertEqual(c_data['full_name'], 'Priya Nair')
        self.assertEqual(c_data['phone'], '9876543210')
        self.assertEqual(c_data['alt_phone'], '9876543211')
        self.assertEqual(c_data['applied_job_id'], self.job.id)
        self.assertEqual(c_data['city'], self.job.location)
        self.assertEqual(c_data['highest_qualification'], 'M.Tech Computer Science')
        self.assertEqual(c_data['current_company'], 'Tech Innovations Ltd')
        self.assertEqual(c_data['technical_skills'], 'Python, Django, AWS, Kubernetes')

        # 4. GET /candidate/register/<token>/ returns pre-filled initial form
        reg_resp = self.client.get(
            reverse('recruitment:candidate_register', kwargs={'token': self.link.token})
        )
        self.assertEqual(reg_resp.status_code, 200)
        self.assertContains(reg_resp, 'Priya Nair')
        self.assertContains(reg_resp, 'priya.nair@gmail.com')
        self.assertContains(reg_resp, '9876543210')
        self.assertContains(reg_resp, '9876543211')
        self.assertContains(reg_resp, 'Google Verified')

        # 5. Verify Talent Roster displays candidate (Google Verified badge removed from table per requirement)
        self.client.force_login(self.hr_user)
        roster_resp = self.client.get(reverse('recruitment:candidates_list'))
        self.assertEqual(roster_resp.status_code, 200)
        self.assertContains(roster_resp, 'Priya Nair')
        self.assertNotContains(roster_resp, 'Google Verified')

        # 6. Verify Candidate Detail Dossier displays Google Verification
        app = JobApplication.objects.filter(candidate=candidate).first()
        detail_resp = self.client.get(reverse('recruitment:candidate_detail', kwargs={'application_id': app.id}))
        self.assertEqual(detail_resp.status_code, 200)
        self.assertContains(detail_resp, 'Google Verified')
        self.assertContains(detail_resp, 'google-oauth2-1029384756')

    def test_job_status_change_and_closed_position_behavior(self):
        # 1. Closed job link will not work on candidate_apply
        closed_job = RecruitmentJob.objects.create(
            title='Archived DevOps Specialist',
            department=self.dept,
            site=self.site,
            location='Pune',
            vacancies=1,
            description='Archived position description.',
            requirements='DevOps skills.',
            status=RecruitmentJob.Status.CLOSED
        )
        resp = self.client.get(reverse('recruitment:candidate_apply') + f'?job={closed_job.id}')
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'recruitment/public/link_invalid.html')
        self.assertContains(resp, 'Registration Link No Longer Active')

        # 2. Closed job link will not work on fast-apply
        fast_resp = self.client.get(reverse('recruitment:candidate_fast_apply') + f'?job={closed_job.id}')
        self.assertEqual(fast_resp.status_code, 200)
        self.assertTemplateUsed(fast_resp, 'recruitment/public/link_invalid.html')

        # 3. Closed job does not appear in universal form positions dropdown
        general_resp = self.client.get(reverse('recruitment:candidate_apply'))
        self.assertEqual(general_resp.status_code, 200)
        self.assertNotContains(general_resp, 'Archived DevOps Specialist')

        # 4. In HR Job Positions table, open job has active link, closed job has disabled link
        self.client.force_login(self.hr_user)
        table_resp = self.client.get(reverse('recruitment:links_list'))
        self.assertEqual(table_resp.status_code, 200)
        self.assertContains(table_resp, 'status-open')
        self.assertContains(table_resp, 'status-closed')
        self.assertContains(table_resp, 'Position is not open - application link is disabled')

    def test_bulk_candidate_status_update(self):
        """
        Verify HR bulk and 1-click status updates for candidate applications,
        auditing in ApplicationStatusHistory, and AJAX response.
        """
        import json
        self.client.force_login(self.hr_user)

        # Create two candidate applications
        cand1 = Candidate.objects.create(full_name='Rahul Varma', email='rahul.varma@example.com', phone='9876543211')
        app1 = JobApplication.objects.create(
            candidate=cand1,
            job=self.job,
            application_type=JobApplication.ApplicationType.ONLINE_FAST_APPLY,
            status=JobApplication.Status.SUBMITTED
        )

        cand2 = Candidate.objects.create(full_name='Ananya Sen', email='ananya.sen@example.com', phone='9876543212')
        app2 = JobApplication.objects.create(
            candidate=cand2,
            job=self.job,
            application_type=JobApplication.ApplicationType.OFFICE_REGISTRATION,
            status=JobApplication.Status.SUBMITTED
        )

        # 1. Bulk update to SHORTLISTED via JSON AJAX
        payload = {
            'application_ids': [app1.id, app2.id],
            'status': JobApplication.Status.SHORTLISTED,
            'notes': 'Selected by HR in initial screening round'
        }
        resp = self.client.post(
            reverse('recruitment:bulk_update_status'),
            data=json.dumps(payload),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['updated_count'], 2)
        self.assertEqual(data['new_status'], 'SHORTLISTED')

        app1.refresh_from_db()
        app2.refresh_from_db()
        self.assertEqual(app1.status, JobApplication.Status.SHORTLISTED)
        self.assertEqual(app2.status, JobApplication.Status.SHORTLISTED)

        # Verify audit history
        hist1 = ApplicationStatusHistory.objects.filter(application=app1, new_status=JobApplication.Status.SHORTLISTED).first()
        self.assertIsNotNone(hist1)
        self.assertEqual(hist1.old_status, JobApplication.Status.SUBMITTED)
        self.assertEqual(hist1.changed_by, self.hr_user)

        # 2. Single 1-click inline status update to INTERVIEW_SCHEDULED
        single_payload = {
            'application_ids': [app1.id],
            'status': JobApplication.Status.INTERVIEW_SCHEDULED,
            'notes': 'Scheduled interview round'
        }
        resp_single = self.client.post(
            reverse('recruitment:bulk_update_status'),
            data=json.dumps(single_payload),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(resp_single.status_code, 200)
        app1.refresh_from_db()
        self.assertEqual(app1.status, JobApplication.Status.INTERVIEW_SCHEDULED)

        # 3. Candidates table renders checkbox, bulk toolbar, and 1-click status dropdown
        table_resp = self.client.get(reverse('recruitment:candidates_list'))
        self.assertEqual(table_resp.status_code, 200)
        self.assertContains(table_resp, 'id="selectAllCandidates"')
        self.assertContains(table_resp, 'candidate-select-checkbox')
        self.assertContains(table_resp, 'id="bulkActionsToolbar"')
        self.assertContains(table_resp, 'id="statusBtn_' + str(app1.id) + '"')
        self.assertContains(table_resp, 'quickUpdateCandidateStatus')
        self.assertContains(table_resp, 'applyBulkStatus')

    def test_schedule_interview_round_section_and_endpoint(self):
        """Verify the Schedule Interview Round section on candidates_list and scheduling endpoint."""
        self.client.login(username='test_hr', password='password123')

        candidate = Candidate.objects.create(
            full_name='Vikram Seth',
            email='vikram.seth@example.com',
            phone='9812345678'
        )
        app = JobApplication.objects.create(
            candidate=candidate,
            job=self.job,
            status=JobApplication.Status.UNDER_REVIEW,
            is_office_registered=True
        )

        # 1. Page renders Schedule Interview Round section and all form controls
        resp = self.client.get(reverse('recruitment:candidates_list'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="scheduleInterviewSection"')
        self.assertContains(resp, 'Schedule Interview Round')
        self.assertContains(resp, 'id="schedInterviewDate"')
        self.assertContains(resp, 'id="schedInterviewTime"')
        self.assertContains(resp, 'id="schedInterviewMode"')
        self.assertContains(resp, 'id="schedInterviewLocation"')
        self.assertContains(resp, 'id="schedInterviewNotes"')
        self.assertContains(resp, 'id="scheduleCandidatePicker"')
        self.assertContains(resp, 'Upcoming Scheduled Interviews')

        # 2. Schedule interview via schedule_candidate_interview endpoint
        schedule_data = {
            'application_ids': [app.id],
            'interview_date': '2026-11-20',
            'interview_time': '14:30',
            'interview_mode': 'VIRTUAL',
            'interview_location_link': 'https://meet.google.com/xyz-abcd-efg',
            'interview_notes': 'Round 1 technical coding assessment'
        }
        post_resp = self.client.post(
            reverse('recruitment:schedule_candidate_interview'),
            data=schedule_data
        )
        self.assertEqual(post_resp.status_code, 302)

        app.refresh_from_db()
        self.assertEqual(app.status, JobApplication.Status.INTERVIEW_SCHEDULED)
        self.assertEqual(str(app.interview_date), '2026-11-20')
        self.assertEqual(str(app.interview_time), '14:30:00')
        self.assertEqual(app.interview_mode, 'VIRTUAL')
        self.assertEqual(app.interview_location_link, 'https://meet.google.com/xyz-abcd-efg')
        self.assertEqual(app.interview_notes, 'Round 1 technical coding assessment')

        # Verify status history log was created
        history_entry = app.status_history.first()
        self.assertIsNotNone(history_entry)
        self.assertEqual(history_entry.new_status, JobApplication.Status.INTERVIEW_SCHEDULED)

        # 3. Verify past dates (yesterday or earlier) are rejected with validation error
        yesterday_str = (timezone.localdate() - timedelta(days=1)).strftime('%Y-%m-%d')
        past_resp = self.client.post(
            reverse('recruitment:schedule_candidate_interview'),
            data={
                'application_ids': [app.id],
                'interview_date': yesterday_str,
                'interview_time': '10:00',
                'interview_mode': 'VIRTUAL',
                'interview_location_link': 'https://meet.google.com/xyz',
            },
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(past_resp.status_code, 400)
        self.assertIn("cannot be in the past", past_resp.json().get('message', ''))

        # 4. Verify past time for today's date is rejected with validation error
        today_str = timezone.localdate().strftime('%Y-%m-%d')
        past_time_resp = self.client.post(
            reverse('recruitment:schedule_candidate_interview'),
            data={
                'application_ids': [app.id],
                'interview_date': today_str,
                'interview_time': '00:01',
                'interview_mode': 'VIRTUAL',
                'interview_location_link': 'https://meet.google.com/xyz',
            },
            headers={'x-requested-with': 'XMLHttpRequest'}
        )
        self.assertEqual(past_time_resp.status_code, 400)
        self.assertIn("interview time cannot be in the past", past_time_resp.json().get('message', ''))

