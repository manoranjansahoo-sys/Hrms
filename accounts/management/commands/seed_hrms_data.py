from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from accounts.models import CustomUser, AuditLog
from organization.models import (
    Department, Designation, Site, Holiday, CompanyEvent,
    Announcement, CompanyPolicy, EventParticipant
)
from employees.models import EmployeeProfile, EmployeeDocument, ProfileCorrectionRequest
from attendance.models import Shift, Attendance, AttendanceCorrectionRequest
from leave_management.models import LeaveType, LeaveBalance, LeaveRequest
from payroll.models import SalaryStructure, PayrollPeriod, Payslip
from performance.models import Goal, PerformanceReview, EmployeeAward
from support.models import OfficialDocumentRequest, SupportTicket, TicketComment, Asset
from notifications.models import Notification


class Command(BaseCommand):
    help = 'Seeds complete, realistic enterprise HRMS demo data with all 4 authorities'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting HRMS enterprise demo data seeding..."))

        today = timezone.localdate()

        # 1. Departments
        dept_eng, _ = Department.objects.get_or_create(
            code='ENG',
            defaults={'name': 'Engineering & Technology', 'description': 'Software architecture, web development, QA and DevOps.'}
        )
        dept_hr, _ = Department.objects.get_or_create(
            code='HR',
            defaults={'name': 'Human Resources', 'description': 'Talent acquisition, employee welfare, payroll, and culture.'}
        )
        dept_prod, _ = Department.objects.get_or_create(
            code='PROD',
            defaults={'name': 'Product & UI/UX Design', 'description': 'Product strategy, wireframing, UX research, and UI design.'}
        )
        dept_ops, _ = Department.objects.get_or_create(
            code='OPS',
            defaults={'name': 'Site Operations & Infrastructure', 'description': 'Facilities, workplace management, IT and compliance.'}
        )
        dept_mkt, _ = Department.objects.get_or_create(
            code='MKT',
            defaults={'name': 'Marketing & Growth', 'description': 'Digital marketing, enterprise branding, sales operations.'}
        )

        # 2. Designations
        desig_head, _ = Designation.objects.get_or_create(
            title='Chief Executive Officer / Managing Director',
            department=dept_ops,
            defaults={'grade_level': 'EXEC-1'}
        )
        desig_hr_head, _ = Designation.objects.get_or_create(
            title='Head of People & HR Operations',
            department=dept_hr,
            defaults={'grade_level': 'L5 - Director'}
        )
        desig_site_mgr, _ = Designation.objects.get_or_create(
            title='Site Operations Manager',
            department=dept_ops,
            defaults={'grade_level': 'L4 - Lead'}
        )
        desig_sr_dev, _ = Designation.objects.get_or_create(
            title='Senior Full-Stack Software Engineer',
            department=dept_eng,
            defaults={'grade_level': 'L3 - Senior'}
        )
        desig_dev, _ = Designation.objects.get_or_create(
            title='Software Engineer (Backend Python)',
            department=dept_eng,
            defaults={'grade_level': 'L2 - Engineer'}
        )
        desig_qa, _ = Designation.objects.get_or_create(
            title='QA Automation Engineer',
            department=dept_eng,
            defaults={'grade_level': 'L2 - Engineer'}
        )
        desig_designer, _ = Designation.objects.get_or_create(
            title='Lead UI/UX Designer',
            department=dept_prod,
            defaults={'grade_level': 'L3 - Senior'}
        )

        # 3. Sites
        site_blr, _ = Site.objects.get_or_create(
            code='BLR-HQ',
            defaults={
                'name': 'Bengaluru HQ Tech Park',
                'city': 'Bengaluru',
                'address': 'Tower 4, Embassy Tech Village, Outer Ring Road, Bengaluru, Karnataka 560103',
                'contact_phone': '+91 80 4912 3000'
            }
        )
        site_hyd, _ = Site.objects.get_or_create(
            code='HYD-CAMPUS',
            defaults={
                'name': 'Hyderabad Innovation Campus',
                'city': 'Hyderabad',
                'address': 'Mindspace Cyberabad, Building 12A, Hitech City, Hyderabad, Telangana 500081',
                'contact_phone': '+91 40 6811 4500'
            }
        )
        site_pune, _ = Site.objects.get_or_create(
            code='PUNE-DC',
            defaults={
                'name': 'Pune Development Center',
                'city': 'Pune',
                'address': 'EON Free Zone, Kharadi, Pune, Maharashtra 411014',
                'contact_phone': '+91 20 4122 8800'
            }
        )

        # 4. Shifts
        shift_gen, _ = Shift.objects.get_or_create(
            name='General Shift',
            defaults={
                'start_time': time(9, 0),
                'end_time': time(18, 0),
                'grace_period_minutes': 15,
                'half_day_hours': Decimal('4.5'),
                'full_day_hours': Decimal('8.0'),
                'is_default': True
            }
        )
        shift_morning, _ = Shift.objects.get_or_create(
            name='Morning Shift',
            defaults={
                'start_time': time(8, 0),
                'end_time': time(17, 0),
                'grace_period_minutes': 15,
                'half_day_hours': Decimal('4.5'),
                'full_day_hours': Decimal('8.0'),
                'is_default': False
            }
        )

        # 5. Users and Authorities
        # Authority 4: Head / Super Admin
        admin_user, _ = CustomUser.objects.get_or_create(
            username='admin',
            defaults={
                'first_name': 'Vikramaditya',
                'last_name': 'Singhania',
                'email': 'head.admin@company.com',
                'role': CustomUser.Role.HEAD,
                'phone': '+91 98201 11223',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('admin123')
        admin_user.role = CustomUser.Role.HEAD
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        # Authority 2: HR Admin
        hr_user, _ = CustomUser.objects.get_or_create(
            username='hr_admin',
            defaults={
                'first_name': 'Pooja',
                'last_name': 'Menon',
                'email': 'pooja.menon@company.com',
                'role': CustomUser.Role.HR,
                'phone': '+91 98450 44556',
                'is_staff': True,
            }
        )
        hr_user.set_password('hr123')
        hr_user.role = CustomUser.Role.HR
        hr_user.is_staff = True
        hr_user.save()

        # Authority 3: Site Manager
        manager_user, _ = CustomUser.objects.get_or_create(
            username='site_manager',
            defaults={
                'first_name': 'Rajesh',
                'last_name': 'Verma',
                'email': 'rajesh.verma@company.com',
                'role': CustomUser.Role.SITE_MANAGER,
                'phone': '+91 98765 67890',
                'is_staff': False,
            }
        )
        manager_user.set_password('mgr123')
        manager_user.role = CustomUser.Role.SITE_MANAGER
        manager_user.save()

        # Assign site manager to Bengaluru HQ
        site_blr.site_manager = manager_user
        site_blr.save()

        # Authority 1: Employee (John Doe - Senior Software Engineer)
        emp_user, _ = CustomUser.objects.get_or_create(
            username='john_doe',
            defaults={
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john.doe@company.com',
                'role': CustomUser.Role.EMPLOYEE,
                'phone': '+91 99001 23456',
            }
        )
        emp_user.set_password('emp123')
        emp_user.role = CustomUser.Role.EMPLOYEE
        emp_user.save()

        # Additional Employees
        emp2_user, _ = CustomUser.objects.get_or_create(
            username='sarah_connor',
            defaults={
                'first_name': 'Sarah',
                'last_name': 'Connor',
                'email': 'sarah.connor@company.com',
                'role': CustomUser.Role.EMPLOYEE,
                'phone': '+91 98111 88990',
            }
        )
        emp2_user.set_password('emp123')
        emp2_user.role = CustomUser.Role.EMPLOYEE
        emp2_user.save()

        emp3_user, _ = CustomUser.objects.get_or_create(
            username='priya_patel',
            defaults={
                'first_name': 'Priya',
                'last_name': 'Patel',
                'email': 'priya.patel@company.com',
                'role': CustomUser.Role.EMPLOYEE,
                'phone': '+91 97234 56789',
            }
        )
        emp3_user.set_password('emp123')
        emp3_user.role = CustomUser.Role.EMPLOYEE
        emp3_user.save()

        emp4_user, _ = CustomUser.objects.get_or_create(
            username='david_miller',
            defaults={
                'first_name': 'David',
                'last_name': 'Miller',
                'email': 'david.miller@company.com',
                'role': CustomUser.Role.EMPLOYEE,
                'phone': '+91 98401 55667',
            }
        )
        emp4_user.set_password('emp123')
        emp4_user.role = CustomUser.Role.EMPLOYEE
        emp4_user.save()

        # 6. Employee Profiles
        # Profile 1: Head Admin
        profile_admin, _ = EmployeeProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                'emp_id': 'EMP001',
                'department': dept_ops,
                'designation': desig_head,
                'site': site_blr,
                'employment_type': EmployeeProfile.EmploymentType.FULL_TIME,
                'joining_date': date(2020, 1, 15),
                'date_of_birth': date(1980, 5, 20),
                'gender': 'MALE',
                'marital_status': 'MARRIED',
                'blood_group': 'O+',
                'bank_name': 'HDFC Bank',
                'bank_account_number': '50100234567891',
                'ifsc_code': 'HDFC0001234',
                'pan_number': 'ABCPS1234F',
                'uan_number': '100902837482',
                'city': 'Bengaluru',
                'address': 'Plot 42, Palm Meadows, Whitefield, Bengaluru',
                'emergency_contact_name': 'Ananya Singhania',
                'emergency_contact_relation': 'Spouse',
                'emergency_contact_phone': '+91 98201 99999',
            }
        )

        # Profile 2: HR Admin
        profile_hr, _ = EmployeeProfile.objects.get_or_create(
            user=hr_user,
            defaults={
                'emp_id': 'EMP002',
                'department': dept_hr,
                'designation': desig_hr_head,
                'site': site_blr,
                'reporting_manager': admin_user,
                'employment_type': EmployeeProfile.EmploymentType.FULL_TIME,
                'joining_date': date(2021, 3, 1),
                'date_of_birth': date(1988, 11, 5), # Birthday soon in November!
                'gender': 'FEMALE',
                'marital_status': 'MARRIED',
                'blood_group': 'B+',
                'bank_name': 'ICICI Bank',
                'bank_account_number': '001205012345',
                'ifsc_code': 'ICIC0000012',
                'pan_number': 'BNMPP8877K',
                'uan_number': '101239847291',
                'city': 'Bengaluru',
                'address': 'Flat 302, Green Glen Layout, Bellandur, Bengaluru',
                'emergency_contact_name': 'Karthik Menon',
                'emergency_contact_relation': 'Spouse',
                'emergency_contact_phone': '+91 98450 11223',
            }
        )

        # Profile 3: Site Manager
        profile_mgr, _ = EmployeeProfile.objects.get_or_create(
            user=manager_user,
            defaults={
                'emp_id': 'EMP003',
                'department': dept_ops,
                'designation': desig_site_mgr,
                'site': site_blr,
                'reporting_manager': admin_user,
                'employment_type': EmployeeProfile.EmploymentType.FULL_TIME,
                'joining_date': date(2021, 8, 15),
                'date_of_birth': date(1985, 11, 2), # Birthday tomorrow or today!
                'gender': 'MALE',
                'marital_status': 'MARRIED',
                'blood_group': 'A+',
                'bank_name': 'State Bank of India',
                'bank_account_number': '201982736451',
                'ifsc_code': 'SBIN0004567',
                'pan_number': 'ASDPV3344J',
                'uan_number': '100847291834',
                'city': 'Bengaluru',
                'address': 'B-704, Prestige Lakeside Habitat, Varthur, Bengaluru',
                'emergency_contact_name': 'Sunita Verma',
                'emergency_contact_relation': 'Spouse',
                'emergency_contact_phone': '+91 98765 11111',
            }
        )

        # Profile 4: John Doe (Senior Software Engineer)
        profile_emp, _ = EmployeeProfile.objects.get_or_create(
            user=emp_user,
            defaults={
                'emp_id': 'EMP101',
                'department': dept_eng,
                'designation': desig_sr_dev,
                'site': site_blr,
                'reporting_manager': manager_user,
                'employment_type': EmployeeProfile.EmploymentType.FULL_TIME,
                'joining_date': date(2022, 4, 10),
                'date_of_birth': date(1994, today.month, today.day), # TODAY IS JOHN'S BIRTHDAY!
                'gender': 'MALE',
                'marital_status': 'SINGLE',
                'blood_group': 'O+',
                'bank_name': 'HDFC Bank',
                'bank_account_number': '50100492817349',
                'ifsc_code': 'HDFC0001827',
                'pan_number': 'DOEPJ1234Q',
                'uan_number': '101928374655',
                'city': 'Bengaluru',
                'address': '124, 5th Main, Indiranagar 1st Stage, Bengaluru, Karnataka 560038',
                'emergency_contact_name': 'Robert Doe',
                'emergency_contact_relation': 'Father',
                'emergency_contact_phone': '+91 99001 99999',
                'education_details': 'B.Tech in Computer Science & Engineering (2012-2016)',
                'experience_summary': '8+ years in full-stack architecture, Django, Python, PostgreSQL, and cloud deployments.',
            }
        )

        # Profile 5: Sarah Connor (Lead UI/UX Designer)
        profile_emp2, _ = EmployeeProfile.objects.get_or_create(
            user=emp2_user,
            defaults={
                'emp_id': 'EMP102',
                'department': dept_prod,
                'designation': desig_designer,
                'site': site_blr,
                'reporting_manager': manager_user,
                'employment_type': EmployeeProfile.EmploymentType.FULL_TIME,
                'joining_date': date(2023, 1, 5),
                'date_of_birth': date(1992, 11, 14),
                'gender': 'FEMALE',
                'marital_status': 'SINGLE',
                'blood_group': 'AB+',
                'bank_name': 'Axis Bank',
                'bank_account_number': '918020038472918',
                'ifsc_code': 'UTIB0000213',
                'pan_number': 'CNRPJ9988X',
                'uan_number': '101827364512',
                'city': 'Bengaluru',
                'address': '45, Koramangala 4th Block, Bengaluru',
                'emergency_contact_name': 'Elena Connor',
                'emergency_contact_relation': 'Mother',
                'emergency_contact_phone': '+91 98111 11223',
            }
        )

        # Profile 6: Priya Patel (QA Automation Engineer)
        profile_emp3, _ = EmployeeProfile.objects.get_or_create(
            user=emp3_user,
            defaults={
                'emp_id': 'EMP103',
                'department': dept_eng,
                'designation': desig_qa,
                'site': site_hyd,
                'reporting_manager': manager_user,
                'employment_type': EmployeeProfile.EmploymentType.FULL_TIME,
                'joining_date': date(2023, 7, 10),
                'date_of_birth': date(1996, 12, 1),
                'gender': 'FEMALE',
                'marital_status': 'SINGLE',
                'blood_group': 'B+',
                'bank_name': 'HDFC Bank',
                'bank_account_number': '50100772211990',
                'ifsc_code': 'HDFC0000456',
                'pan_number': 'PTLPK6655M',
                'uan_number': '101928471625',
                'city': 'Hyderabad',
                'address': 'Road No 36, Jubilee Hills, Hyderabad',
                'emergency_contact_name': 'Ramesh Patel',
                'emergency_contact_relation': 'Father',
                'emergency_contact_phone': '+91 97234 11122',
            }
        )

        # Profile 7: David Miller (Backend Python Engineer)
        profile_emp4, _ = EmployeeProfile.objects.get_or_create(
            user=emp4_user,
            defaults={
                'emp_id': 'EMP104',
                'department': dept_eng,
                'designation': desig_dev,
                'site': site_pune,
                'reporting_manager': manager_user,
                'employment_type': EmployeeProfile.EmploymentType.FULL_TIME,
                'joining_date': date(2024, 2, 1),
                'date_of_birth': date(1997, 8, 22),
                'gender': 'MALE',
                'marital_status': 'SINGLE',
                'blood_group': 'O-',
                'bank_name': 'Kotak Mahindra Bank',
                'bank_account_number': '411002938472',
                'ifsc_code': 'KKBK0000123',
                'pan_number': 'MLRDK3322L',
                'uan_number': '102938475612',
                'city': 'Pune',
                'address': 'Magarpatta Cybercity, Hadapsar, Pune',
                'emergency_contact_name': 'Susan Miller',
                'emergency_contact_relation': 'Sister',
                'emergency_contact_phone': '+91 98401 22334',
            }
        )

        # 7. Leave Types & Balances
        lt_cl, _ = LeaveType.objects.get_or_create(
            code='CL',
            defaults={'name': 'Casual Leave', 'days_per_year': Decimal('12.0'), 'is_paid': True, 'description': 'For unplanned personal affairs, casual events.'}
        )
        lt_sl, _ = LeaveType.objects.get_or_create(
            code='SL',
            defaults={'name': 'Sick Leave', 'days_per_year': Decimal('10.0'), 'is_paid': True, 'requires_attachment': True, 'description': 'Medical illness or health consultations.'}
        )
        lt_el, _ = LeaveType.objects.get_or_create(
            code='EL',
            defaults={'name': 'Earned / Privilege Leave', 'days_per_year': Decimal('15.0'), 'is_paid': True, 'description': 'Planned vacations and annual rest leaves.'}
        )
        lt_lop, _ = LeaveType.objects.get_or_create(
            code='LOP',
            defaults={'name': 'Loss of Pay (Unpaid Leave)', 'days_per_year': Decimal('0.0'), 'is_paid': False, 'description': 'Leaves taken without paid quota balance.'}
        )

        all_profiles = [profile_admin, profile_hr, profile_mgr, profile_emp, profile_emp2, profile_emp3, profile_emp4]
        for p in all_profiles:
            LeaveBalance.objects.get_or_create(
                employee=p, leave_type=lt_cl, year=2026,
                defaults={'allocated_days': Decimal('12.0'), 'used_days': Decimal('2.0'), 'pending_days': Decimal('0.0')}
            )
            LeaveBalance.objects.get_or_create(
                employee=p, leave_type=lt_sl, year=2026,
                defaults={'allocated_days': Decimal('10.0'), 'used_days': Decimal('1.0'), 'pending_days': Decimal('0.0')}
            )
            LeaveBalance.objects.get_or_create(
                employee=p, leave_type=lt_el, year=2026,
                defaults={'allocated_days': Decimal('15.0'), 'used_days': Decimal('3.0'), 'pending_days': Decimal('0.0')}
            )

        # Sample Leave Requests
        # 1. John Doe pending leave request (For Site Manager to review!)
        LeaveRequest.objects.get_or_create(
            employee=profile_emp,
            start_date=today + timedelta(days=5),
            end_date=today + timedelta(days=6),
            defaults={
                'leave_type': lt_cl,
                'total_days': Decimal('2.0'),
                'reason': 'Attending family celebration and personal commitments.',
                'status': LeaveRequest.Status.PENDING_MANAGER,
                'manager_decision': 'PENDING',
                'hr_decision': 'PENDING',
            }
        )
        # 2. Sarah Connor leave pending HR approval
        LeaveRequest.objects.get_or_create(
            employee=profile_emp2,
            start_date=today + timedelta(days=10),
            end_date=today + timedelta(days=12),
            defaults={
                'leave_type': lt_el,
                'total_days': Decimal('3.0'),
                'reason': 'Annual family vacation trip to Himachal.',
                'status': LeaveRequest.Status.PENDING_HR,
                'manager_decision': 'RECOMMENDED',
                'manager_remarks': 'Team workload covered by Priya and David. Recommended.',
                'manager_action_by': manager_user,
                'manager_action_at': timezone.now() - timedelta(days=1),
                'hr_decision': 'PENDING',
            }
        )
        # 3. David Miller approved past leave
        LeaveRequest.objects.get_or_create(
            employee=profile_emp4,
            start_date=today - timedelta(days=14),
            end_date=today - timedelta(days=14),
            defaults={
                'leave_type': lt_sl,
                'total_days': Decimal('1.0'),
                'reason': 'Viral fever and doctor consultation.',
                'status': LeaveRequest.Status.APPROVED,
                'manager_decision': 'RECOMMENDED',
                'manager_action_by': manager_user,
                'hr_decision': 'APPROVED',
                'hr_action_by': hr_user,
                'hr_remarks': 'Approved as per medical certificate.',
                'hr_action_at': timezone.now() - timedelta(days=13),
            }
        )

        # 8. Company Holidays
        Holiday.objects.get_or_create(
            date=date(2026, 1, 26),
            defaults={'title': 'Republic Day', 'holiday_type': Holiday.HolidayType.PUBLIC, 'description': 'National celebration of the Constitution of India.'}
        )
        Holiday.objects.get_or_create(
            date=date(2026, 3, 25),
            defaults={'title': 'Holi (Festival of Colours)', 'holiday_type': Holiday.HolidayType.FESTIVAL, 'description': 'Spring festival celebrated nationwide.'}
        )
        Holiday.objects.get_or_create(
            date=date(2026, 8, 15),
            defaults={'title': 'Independence Day', 'holiday_type': Holiday.HolidayType.PUBLIC, 'description': '79th Indian Independence Day celebration.'}
        )
        Holiday.objects.get_or_create(
            date=date(2026, 10, 2),
            defaults={'title': 'Mahatma Gandhi Jayanti', 'holiday_type': Holiday.HolidayType.PUBLIC, 'description': 'Honoring the Father of the Nation.'}
        )
        Holiday.objects.get_or_create(
            date=date(2026, 11, 10),
            defaults={'title': 'Diwali (Deepavali)', 'holiday_type': Holiday.HolidayType.FESTIVAL, 'description': 'Festival of lights and prosperity.'}
        )
        Holiday.objects.get_or_create(
            date=date(2026, 12, 25),
            defaults={'title': 'Christmas Day', 'holiday_type': Holiday.HolidayType.FESTIVAL, 'description': 'Christmas celebrations and year-end holidays.'}
        )
        Holiday.objects.get_or_create(
            date=date(2026, 12, 31),
            defaults={'title': 'Company Annual Founder Day', 'holiday_type': Holiday.HolidayType.COMPANY, 'description': 'Foundation Day corporate celebration.'}
        )

        # 9. Company Announcements
        Announcement.objects.get_or_create(
            title='Annual Performance Review Cycle 2026 Open',
            defaults={
                'category': 'MANAGEMENT',
                'priority': 'HIGH',
                'is_pinned': True,
                'created_by': admin_user,
                'content': 'We are pleased to announce the kick-off of our Annual Performance Review Cycle. All employees and site managers are requested to complete self-appraisals and goal validations by the end of this month in the Performance module.'
            }
        )
        Announcement.objects.get_or_create(
            title='Comprehensive Group Health Insurance Policy Renewal',
            defaults={
                'category': 'HR',
                'priority': 'MEDIUM',
                'is_pinned': True,
                'created_by': hr_user,
                'content': 'The company has renewed our corporate health coverage with upgraded parental benefits and enhanced cashless network hospitals. Please check your HRMS Document Vault for policy details and e-cards.'
            }
        )
        Announcement.objects.get_or_create(
            title='Bangalore HQ Office Cafeteria Upgrade & New Menu',
            defaults={
                'category': 'GENERAL',
                'priority': 'LOW',
                'is_pinned': False,
                'created_by': hr_user,
                'target_site': site_blr,
                'content': 'Starting this Monday, the Bengaluru HQ cafeteria features an expanded organic salad bar, live gourmet espresso stations, and diverse regional lunch offerings.'
            }
        )
        Announcement.objects.get_or_create(
            title='Emergency IT Security Advisory: Mandatory MFA Verification',
            defaults={
                'category': 'EMERGENCY',
                'priority': 'URGENT',
                'is_pinned': True,
                'created_by': admin_user,
                'content': 'All team members must ensure two-factor authentication is active on work email accounts and VPN clients. Report any phishing anomalies to the IT Support Desk immediately.'
            }
        )

        # 10. Official Events
        event1, _ = CompanyEvent.objects.get_or_create(
            title='Annual Tech Symposium & Hackathon 2026',
            defaults={
                'event_type': 'TRAINING',
                'venue': 'Main Auditorium, Bengaluru HQ Tech Park & Virtual Stream',
                'start_datetime': timezone.now() + timedelta(days=12, hours=9),
                'end_datetime': timezone.now() + timedelta(days=13, hours=18),
                'description': '48-hour internal hackathon focusing on AI-assisted enterprise workflows, microservices optimization, and developer productivity tools.',
                'created_by': hr_user
            }
        )
        event2, _ = CompanyEvent.objects.get_or_create(
            title='Diwali Grand Corporate Celebration & Cultural Evening',
            defaults={
                'event_type': 'CELEBRATION',
                'venue': 'Open Lawn Pavilion, Bengaluru & Campus Hubs',
                'start_datetime': timezone.now() + timedelta(days=8, hours=17),
                'end_datetime': timezone.now() + timedelta(days=8, hours=22),
                'description': 'Traditional festive celebration featuring ethnic attire contests, musical performances, rangoli competitions, and a banquet dinner.',
                'created_by': hr_user
            }
        )
        EventParticipant.objects.get_or_create(event=event1, user=emp_user)
        EventParticipant.objects.get_or_create(event=event2, user=emp_user)

        # 11. Company Policies
        CompanyPolicy.objects.get_or_create(
            title='Code of Conduct & Workplace Ethics Policy',
            defaults={
                'category': 'Ethics & Governance',
                'summary': 'Mandatory corporate policy defining our commitment to integrity, diversity, non-discrimination, anti-harassment, and mutual respect.',
                'effective_date': date(2026, 1, 1),
                'requires_acknowledgement': True
            }
        )
        CompanyPolicy.objects.get_or_create(
            title='Flexible Remote & Hybrid Work Policy',
            defaults={
                'category': 'Workplace Operations',
                'summary': 'Guidelines on core business hours, office attendance frequency, ergonomics, and communication etiquette for hybrid workers.',
                'effective_date': date(2026, 1, 1),
                'requires_acknowledgement': False
            }
        )
        CompanyPolicy.objects.get_or_create(
            title='Information Security & Clean Desk Policy',
            defaults={
                'category': 'IT & Data Security',
                'summary': 'Protocols on safeguarding confidential employee and client data, physical workstation security, password governance, and data classification.',
                'effective_date': date(2026, 1, 1),
                'requires_acknowledgement': True
            }
        )

        # 12. Employee Awards / Recognitions
        EmployeeAward.objects.get_or_create(
            employee=profile_emp,
            award_title='Employee of the Month',
            month_year='October 2026',
            defaults={
                'citation': 'Exceptional leadership in architecting and delivering the High-Performance Core API Module ahead of schedule with zero defect leakage.',
                'awarded_by': admin_user,
                'is_featured': True
            }
        )
        EmployeeAward.objects.get_or_create(
            employee=profile_emp3,
            award_title='Quality Champion Award',
            month_year='September 2026',
            defaults={
                'citation': 'Pioneered an end-to-end automated testing regression pipeline that reduced deployment release cycles by 40%.',
                'awarded_by': manager_user,
                'is_featured': True
            }
        )

        # 13. Salary Structures
        # John Doe (EMP101) - Gross 1,20,000 / month
        SalaryStructure.objects.get_or_create(
            employee=profile_emp,
            defaults={
                'basic_salary': Decimal('60000.00'),
                'hra': Decimal('30000.00'),
                'conveyance_allowance': Decimal('5000.00'),
                'medical_allowance': Decimal('5000.00'),
                'special_allowance': Decimal('20000.00'),
                'provident_fund': Decimal('7200.00'),
                'professional_tax': Decimal('200.00'),
                'tds': Decimal('8500.00'),
            }
        )
        # Sarah Connor (EMP102) - Gross 95,000 / month
        SalaryStructure.objects.get_or_create(
            employee=profile_emp2,
            defaults={
                'basic_salary': Decimal('47500.00'),
                'hra': Decimal('23750.00'),
                'conveyance_allowance': Decimal('4000.00'),
                'medical_allowance': Decimal('4000.00'),
                'special_allowance': Decimal('15750.00'),
                'provident_fund': Decimal('5700.00'),
                'professional_tax': Decimal('200.00'),
                'tds': Decimal('5500.00'),
            }
        )
        # Priya Patel (EMP103) - Gross 80,000 / month
        SalaryStructure.objects.get_or_create(
            employee=profile_emp3,
            defaults={
                'basic_salary': Decimal('40000.00'),
                'hra': Decimal('20000.00'),
                'conveyance_allowance': Decimal('3500.00'),
                'medical_allowance': Decimal('3500.00'),
                'special_allowance': Decimal('13000.00'),
                'provident_fund': Decimal('4800.00'),
                'professional_tax': Decimal('200.00'),
                'tds': Decimal('4000.00'),
            }
        )
        # David Miller (EMP104) - Gross 75,000 / month
        SalaryStructure.objects.get_or_create(
            employee=profile_emp4,
            defaults={
                'basic_salary': Decimal('37500.00'),
                'hra': Decimal('18750.00'),
                'conveyance_allowance': Decimal('3500.00'),
                'medical_allowance': Decimal('3500.00'),
                'special_allowance': Decimal('11750.00'),
                'provident_fund': Decimal('4500.00'),
                'professional_tax': Decimal('200.00'),
                'tds': Decimal('3500.00'),
            }
        )
        # Site Manager Rajesh Verma - Gross 1,50,000 / month
        SalaryStructure.objects.get_or_create(
            employee=profile_mgr,
            defaults={
                'basic_salary': Decimal('75000.00'),
                'hra': Decimal('37500.00'),
                'conveyance_allowance': Decimal('6000.00'),
                'medical_allowance': Decimal('6000.00'),
                'special_allowance': Decimal('25500.00'),
                'provident_fund': Decimal('9000.00'),
                'professional_tax': Decimal('200.00'),
                'tds': Decimal('14500.00'),
            }
        )

        # 14. Monthly Payroll & Payslips
        # Processed Payroll for Last Month (October 2026)
        payroll_oct, _ = PayrollPeriod.objects.get_or_create(
            month=10,
            year=2026,
            defaults={
                'working_days': 26,
                'status': 'APPROVED',
                'total_gross': Decimal('520000.00'),
                'total_deductions': Decimal('65000.00'),
                'total_net': Decimal('455000.00'),
                'processed_by': hr_user,
                'approved_by': admin_user,
                'approved_at': timezone.now() - timedelta(days=2),
            }
        )

        # Payslip for John Doe
        Payslip.objects.get_or_create(
            payroll_period=payroll_oct,
            employee=profile_emp,
            defaults={
                'month': 10,
                'year': 2026,
                'total_working_days': Decimal('26.0'),
                'present_days': Decimal('24.0'),
                'paid_leaves': Decimal('2.0'),
                'loss_of_pay_days': Decimal('0.0'),
                'payable_days': Decimal('26.0'),
                'basic_salary': Decimal('60000.00'),
                'hra': Decimal('30000.00'),
                'conveyance_allowance': Decimal('5000.00'),
                'medical_allowance': Decimal('5000.00'),
                'special_allowance': Decimal('20000.00'),
                'bonus': Decimal('10000.00'),
                'gross_earnings': Decimal('130000.00'),
                'provident_fund': Decimal('7200.00'),
                'professional_tax': Decimal('200.00'),
                'tds': Decimal('8500.00'),
                'other_deductions': Decimal('0.00'),
                'total_deductions': Decimal('15900.00'),
                'net_payable': Decimal('114100.00'),
                'status': 'APPROVED',
                'payment_date': date(2026, 10, 31),
                'payment_method': 'DIRECT_BANK_TRANSFER',
                'transaction_ref': 'NEFT-HDFC-9928172635',
            }
        )

        # Payslip for Sarah Connor
        Payslip.objects.get_or_create(
            payroll_period=payroll_oct,
            employee=profile_emp2,
            defaults={
                'month': 10,
                'year': 2026,
                'total_working_days': Decimal('26.0'),
                'present_days': Decimal('25.0'),
                'paid_leaves': Decimal('1.0'),
                'payable_days': Decimal('26.0'),
                'basic_salary': Decimal('47500.00'),
                'hra': Decimal('23750.00'),
                'conveyance_allowance': Decimal('4000.00'),
                'medical_allowance': Decimal('4000.00'),
                'special_allowance': Decimal('15750.00'),
                'bonus': Decimal('0.00'),
                'gross_earnings': Decimal('95000.00'),
                'provident_fund': Decimal('5700.00'),
                'professional_tax': Decimal('200.00'),
                'tds': Decimal('5500.00'),
                'total_deductions': Decimal('11400.00'),
                'net_payable': Decimal('83600.00'),
                'status': 'APPROVED',
                'payment_date': date(2026, 10, 31),
                'transaction_ref': 'NEFT-AXIS-8827163542',
            }
        )

        # 15. Attendance Records (Recent days including Today)
        # Today's attendance for John Doe (Present, punched in at 9:02 AM)
        today_start = timezone.now().replace(hour=9, minute=2, second=0, microsecond=0)
        Attendance.objects.get_or_create(
            employee=profile_emp,
            date=today,
            defaults={
                'shift': shift_gen,
                'punch_in': today_start,
                'punch_out': None,
                'working_hours': Decimal('6.50'),
                'status': 'PRESENT',
                'is_late': False,
                'device_source': 'WEB',
                'punch_in_ip': '192.168.1.45',
            }
        )
        # Sarah Connor (Punched in at 9:25 AM - Late arrival!)
        Attendance.objects.get_or_create(
            employee=profile_emp2,
            date=today,
            defaults={
                'shift': shift_gen,
                'punch_in': timezone.now().replace(hour=9, minute=25, second=0),
                'punch_out': None,
                'working_hours': Decimal('6.10'),
                'status': 'PRESENT',
                'is_late': True,
                'device_source': 'WEB',
                'punch_in_ip': '192.168.1.88',
                'notes': 'Traffic delay at Silk Board junction.'
            }
        )
        # Priya Patel (Present at Hyderabad)
        Attendance.objects.get_or_create(
            employee=profile_emp3,
            date=today,
            defaults={
                'shift': shift_gen,
                'punch_in': timezone.now().replace(hour=8, minute=55, second=0),
                'working_hours': Decimal('6.60'),
                'status': 'PRESENT',
                'is_late': False,
                'device_source': 'KIOSK',
                'punch_in_ip': '10.20.4.12',
            }
        )
        # David Miller (On Leave today)
        Attendance.objects.get_or_create(
            employee=profile_emp4,
            date=today,
            defaults={
                'shift': shift_gen,
                'status': 'ON_LEAVE',
                'working_hours': Decimal('0.00'),
                'notes': 'Approved Casual Leave.'
            }
        )

        # Historical attendance records for John Doe for the past 5 days
        for i in range(1, 6):
            past_date = today - timedelta(days=i)
            # Skip Sunday
            if past_date.weekday() == 6:
                Attendance.objects.get_or_create(
                    employee=profile_emp,
                    date=past_date,
                    defaults={'status': 'WEEK_OFF', 'working_hours': Decimal('0.00')}
                )
                continue

            pin = timezone.now().replace(year=past_date.year, month=past_date.month, day=past_date.day, hour=9, minute=10, second=0)
            pout = pin + timedelta(hours=8, minutes=45)
            Attendance.objects.get_or_create(
                employee=profile_emp,
                date=past_date,
                defaults={
                    'shift': shift_gen,
                    'punch_in': pin,
                    'punch_out': pout,
                    'working_hours': Decimal('8.75'),
                    'overtime_hours': Decimal('0.75'),
                    'status': 'PRESENT',
                    'is_late': False,
                    'device_source': 'WEB',
                }
            )

        # Attendance Correction Request (David Miller requested correction for missing punch out)
        missing_punch_date = today - timedelta(days=4)
        att_david, _ = Attendance.objects.get_or_create(
            employee=profile_emp4,
            date=missing_punch_date,
            defaults={
                'shift': shift_gen,
                'punch_in': timezone.now().replace(year=missing_punch_date.year, month=missing_punch_date.month, day=missing_punch_date.day, hour=9, minute=5),
                'punch_out': None,
                'status': 'HALF_DAY',
                'working_hours': Decimal('4.00')
            }
        )
        AttendanceCorrectionRequest.objects.get_or_create(
            employee=profile_emp4,
            date=missing_punch_date,
            defaults={
                'attendance': att_david,
                'requested_punch_in': att_david.punch_in,
                'requested_punch_out': att_david.punch_in + timedelta(hours=8, minutes=30),
                'reason': 'Accidental omission of punch out due to emergency client release call at 6:00 PM.',
                'status': 'PENDING',
            }
        )

        # 16. Goals & Performance Reviews
        Goal.objects.get_or_create(
            employee=profile_emp,
            title='Implement Microservices Event Bus Architecture',
            defaults={
                'description': 'Refactor monolithic order communication pipeline to asynchronous event-driven architecture using Celery and Redis.',
                'target_date': date(2026, 12, 15),
                'status': 'IN_PROGRESS',
                'progress_percentage': 75,
                'assigned_by': manager_user
            }
        )
        Goal.objects.get_or_create(
            employee=profile_emp,
            title='Mentor Junior Developers in Django ORM Optimization',
            defaults={
                'description': 'Conduct bi-weekly code review workshops on query reduction, select_related, and indexing strategies.',
                'target_date': date(2026, 11, 30),
                'status': 'IN_PROGRESS',
                'progress_percentage': 60,
                'assigned_by': manager_user
            }
        )
        PerformanceReview.objects.get_or_create(
            employee=profile_emp,
            review_cycle='Mid-Year Review 2026',
            defaults={
                'reviewer': manager_user,
                'rating': 5,
                'strengths': 'Exceptional problem-solving capabilities, proactive technical mentorship, and flawless production delivery.',
                'areas_for_improvement': 'Can delegate low-level routine bug fixes more effectively to focus on enterprise systems architecture.',
                'manager_remarks': 'Outstanding contributor. A cornerstone of the Engineering team.',
                'recommendation': 'PROMOTION',
                'status': 'APPROVED'
            }
        )

        # 17. Support Tickets & Service Requests
        SupportTicket.objects.get_or_create(
            employee=profile_emp,
            subject='Additional 32-inch 4K Monitor Request for Multi-Display Setup',
            defaults={
                'category': 'IT_SUPPORT',
                'priority': 'MEDIUM',
                'description': 'Requesting secondary high-resolution display for backend microservices profiling and monitoring dashboards.',
                'status': 'IN_PROGRESS',
                'assigned_to': admin_user
            }
        )
        OfficialDocumentRequest.objects.get_or_create(
            employee=profile_emp,
            document_type='EMPLOYMENT_CERTIFICATE',
            defaults={
                'purpose': 'Required for housing loan documentation submission to HDFC Bank.',
                'status': 'PENDING'
            }
        )
        OfficialDocumentRequest.objects.get_or_create(
            employee=profile_emp2,
            document_type='EXPERIENCE_LETTER',
            defaults={
                'purpose': 'Visa and passport renewal verification.',
                'status': 'ISSUED',
                'hr_remarks': 'Certificate generated and countersigned.',
                'reviewed_by': hr_user,
                'resolved_at': timezone.now() - timedelta(days=5)
            }
        )

        # 18. Corporate Assets
        Asset.objects.get_or_create(
            asset_tag='AST-BLR-0101',
            defaults={
                'name': 'MacBook Pro 16" M3 Max (36GB RAM / 1TB SSD)',
                'asset_type': 'LAPTOP',
                'serial_number': 'C02G8712MD6R',
                'assigned_to': profile_emp,
                'assigned_date': date(2022, 4, 11),
                'status': 'ASSIGNED',
                'specifications': 'Apple M3 Max 14-core CPU, 30-core GPU, 36GB Unified Memory, Space Black'
            }
        )
        Asset.objects.get_or_create(
            asset_tag='AST-BLR-0102',
            defaults={
                'name': 'Dell UltraSharp 27" 4K USB-C Hub Monitor',
                'asset_type': 'MONITOR',
                'serial_number': 'CN-0N374M-74261',
                'assigned_to': profile_emp,
                'assigned_date': date(2022, 4, 15),
                'status': 'ASSIGNED',
            }
        )
        Asset.objects.get_or_create(
            asset_tag='AST-BLR-0205',
            defaults={
                'name': 'ThinkPad P16s Gen 2 AMD Ryzen 7 PRO',
                'asset_type': 'LAPTOP',
                'serial_number': 'PF430291',
                'status': 'AVAILABLE',
                'specifications': 'Ryzen 7 PRO 7840U, 32GB LPDDR5x, 1TB NVMe Gen4'
            }
        )

        # 19. Notifications for John Doe
        Notification.objects.get_or_create(
            recipient=emp_user,
            title='🎉 Happy Birthday, John!',
            defaults={
                'message': 'The entire company family wishes you a fabulous birthday and a stellar year of success, health, and happiness!',
                'notification_type': 'BIRTHDAY',
                'target_url': '/portal/',
                'is_read': False
            }
        )
        Notification.objects.get_or_create(
            recipient=emp_user,
            title='October 2026 Payslip Available',
            defaults={
                'message': 'Your salary for October 2026 has been processed and disbursed. Click to view or download your detailed PDF payslip.',
                'notification_type': 'PAYROLL',
                'target_url': '/payroll/my-payslips/',
                'is_read': False
            }
        )
        Notification.objects.get_or_create(
            recipient=emp_user,
            title='New Company Announcement: Annual Tech Symposium',
            defaults={
                'message': 'Registrations are now open for the Annual Tech Symposium & Hackathon 2026. Register your squad!',
                'notification_type': 'EVENT',
                'target_url': '/portal/events/',
                'is_read': True
            }
        )

        # Notifications for Site Manager
        Notification.objects.get_or_create(
            recipient=manager_user,
            title='Action Required: 1 New Leave Request',
            defaults={
                'message': 'John Doe (EMP101) has applied for 2 days Casual Leave starting next week.',
                'notification_type': 'LEAVE',
                'target_url': '/dashboard/site-manager/leave-approvals/',
                'is_read': False
            }
        )
        Notification.objects.get_or_create(
            recipient=manager_user,
            title='Attendance Correction Request',
            defaults={
                'message': 'David Miller has submitted a missing punch out correction for your review.',
                'notification_type': 'ATTENDANCE',
                'target_url': '/dashboard/site-manager/attendance-corrections/',
                'is_read': False
            }
        )

        # Notifications for HR
        Notification.objects.get_or_create(
            recipient=hr_user,
            title='Leave Request Forwarded by Site Manager',
            defaults={
                'message': 'Sarah Connor (EMP102) Earned Leave request recommended by Site Manager Rajesh Verma. Awaiting HR approval.',
                'notification_type': 'LEAVE',
                'target_url': '/dashboard/hr/leave-requests/',
                'is_read': False
            }
        )

        # 20. Audit Log entries
        AuditLog.objects.get_or_create(
            action='PAYROLL',
            module='Payroll Management',
            description='October 2026 monthly company-wide payroll processed by HR Admin Pooja Menon.',
            defaults={'user': hr_user, 'ip_address': '192.168.1.10'}
        )
        AuditLog.objects.get_or_create(
            action='APPROVAL',
            module='Executive Approvals',
            description='October 2026 monthly payroll approved by Head of Company Vikramaditya Singhania.',
            defaults={'user': admin_user, 'ip_address': '192.168.1.2'}
        )

        # 21. Recruitment & Candidate Portal demo data
        from django.core.management import call_command
        try:
            call_command('seed_recruitment_data')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Could not seed recruitment data: {e}"))

        self.stdout.write(self.style.SUCCESS("HRMS Enterprise demo data seeded successfully!"))
        self.stdout.write(self.style.SUCCESS("""
Credentials for testing all 4 authorities:
  1. Head / Super Admin : Username: 'admin'        | Password: 'admin123' (Role: head)
  2. HR Administrator   : Username: 'hr_admin'     | Password: 'hr123'    (Role: hr)
  3. Site Manager       : Username: 'site_manager' | Password: 'mgr123'   (Role: site_manager)
  4. Employee           : Username: 'john_doe'     | Password: 'emp123'   (Role: employee)
        """))

