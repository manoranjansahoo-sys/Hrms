from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from organization.models import Department, Designation, Site
from employees.models import EmployeeProfile
from support.models import OfficialDocumentRequest


class DocumentRequestWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name='Human Resources', code='HR')
        self.desig = Designation.objects.create(title='HR Specialist', department=self.dept)
        self.site = Site.objects.create(name='Headquarters', code='HQ-1', city='New Delhi')

        # 1. Head / Admin User
        self.admin_user = CustomUser.objects.create_user(
            username='admin_boss',
            email='admin@example.com',
            role=CustomUser.Role.HEAD,
            password='AdminPassword123'
        )

        # 2. HR User 1
        self.hr_user_1 = CustomUser.objects.create_user(
            username='hr_priya',
            email='priya@example.com',
            role=CustomUser.Role.HR,
            first_name='Priya',
            last_name='Sharma',
            password='HrPassword123'
        )
        self.hr_profile_1 = EmployeeProfile.objects.create(
            user=self.hr_user_1,
            emp_id='HR-001',
            department=self.dept,
            designation=self.desig,
            site=self.site,
            gender='FEMALE',
            joining_date='2024-01-01'
        )

        # 3. HR User 2 (Peer)
        self.hr_user_2 = CustomUser.objects.create_user(
            username='hr_rahul',
            email='rahul@example.com',
            role=CustomUser.Role.HR,
            first_name='Rahul',
            last_name='Verma',
            password='HrPassword123'
        )
        self.hr_profile_2 = EmployeeProfile.objects.create(
            user=self.hr_user_2,
            emp_id='HR-002',
            department=self.dept,
            designation=self.desig,
            site=self.site,
            gender='MALE',
            joining_date='2024-02-01'
        )

        # 4. Regular Employee
        self.emp_user = CustomUser.objects.create_user(
            username='emp_arjun',
            email='arjun@example.com',
            role=CustomUser.Role.EMPLOYEE,
            first_name='Arjun',
            last_name='Patel',
            password='EmpPassword123'
        )
        self.emp_profile = EmployeeProfile.objects.create(
            user=self.emp_user,
            emp_id='EMP-100',
            department=self.dept,
            designation=self.desig,
            site=self.site,
            gender='MALE',
            joining_date='2024-03-01'
        )

    def test_regular_employee_submits_document_request(self):
        """Regular employee requests a document; notification routes to HR and Admin."""
        self.client.login(username='emp_arjun', password='EmpPassword123')
        response = self.client.post(reverse('support:documents_list'), {
            'document_type': 'EMPLOYMENT_CERTIFICATE',
            'purpose': 'Visa application proof of employment',
        })
        self.assertRedirects(response, reverse('support:documents_list'))

        doc_req = OfficialDocumentRequest.objects.get(employee=self.emp_profile)
        self.assertEqual(doc_req.document_type, 'EMPLOYMENT_CERTIFICATE')
        self.assertEqual(doc_req.status, 'PENDING')

    def test_hr_submits_document_request_for_self(self):
        """HR requests a document for self; should route to Admin without NameError on Q."""
        self.client.login(username='hr_priya', password='HrPassword123')
        response = self.client.post(reverse('support:documents_list'), {
            'document_type': 'SALARY_CERTIFICATE',
            'purpose': 'Bank loan verification',
        })
        self.assertRedirects(response, reverse('support:documents_list'))

        doc_req = OfficialDocumentRequest.objects.get(employee=self.hr_profile_1)
        self.assertEqual(doc_req.document_type, 'SALARY_CERTIFICATE')
        self.assertEqual(doc_req.status, 'PENDING')

    def test_hr_cannot_self_approve_document_request(self):
        """HR cannot approve their own document request."""
        doc_req = OfficialDocumentRequest.objects.create(
            employee=self.hr_profile_1,
            document_type='EXPERIENCE_LETTER',
            purpose='Future reference',
            status='PENDING'
        )

        self.client.login(username='hr_priya', password='HrPassword123')
        response = self.client.post(reverse('support:process_document', args=[doc_req.id]), {
            'action': 'ISSUE',
            'remarks': 'Self approving'
        })
        self.assertRedirects(response, reverse('support:documents_list'))

        doc_req.refresh_from_db()
        self.assertEqual(doc_req.status, 'PENDING')

    def test_peer_hr_cannot_approve_hr_document_request(self):
        """Another HR cannot approve an HR staff member's request; only Admin can."""
        doc_req = OfficialDocumentRequest.objects.create(
            employee=self.hr_profile_1,
            document_type='BONAFIDE',
            purpose='Passport renewal',
            status='PENDING'
        )

        self.client.login(username='hr_rahul', password='HrPassword123')
        response = self.client.post(reverse('support:process_document', args=[doc_req.id]), {
            'action': 'ISSUE',
            'remarks': 'Peer HR approving'
        })
        self.assertRedirects(response, reverse('support:documents_list'))

        doc_req.refresh_from_db()
        self.assertEqual(doc_req.status, 'PENDING')

    def test_admin_can_approve_hr_document_request(self):
        """Admin (Head) can approve and issue document request for HR staff."""
        doc_req = OfficialDocumentRequest.objects.create(
            employee=self.hr_profile_1,
            document_type='SALARY_CERTIFICATE',
            purpose='Bank verification',
            status='PENDING'
        )

        self.client.login(username='admin_boss', password='AdminPassword123')
        response = self.client.post(reverse('support:process_document', args=[doc_req.id]), {
            'action': 'ISSUE',
            'remarks': 'Approved by Management'
        })
        self.assertRedirects(response, reverse('support:documents_list'))

        doc_req.refresh_from_db()
        self.assertEqual(doc_req.status, 'ISSUED')
        self.assertEqual(doc_req.reviewed_by, self.admin_user)
        self.assertEqual(doc_req.hr_remarks, 'Approved by Management')

    def test_hr_can_approve_regular_employee_document_request(self):
        """HR can approve regular employee document request."""
        doc_req = OfficialDocumentRequest.objects.create(
            employee=self.emp_profile,
            document_type='EMPLOYMENT_CERTIFICATE',
            purpose='Rental lease proof',
            status='PENDING'
        )

        self.client.login(username='hr_priya', password='HrPassword123')
        response = self.client.post(reverse('support:process_document', args=[doc_req.id]), {
            'action': 'ISSUE',
            'remarks': 'Issued by HR'
        })
        self.assertRedirects(response, reverse('support:documents_list'))

        doc_req.refresh_from_db()
        self.assertEqual(doc_req.status, 'ISSUED')
        self.assertEqual(doc_req.reviewed_by, self.hr_user_1)
