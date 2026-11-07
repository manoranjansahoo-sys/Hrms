import os
from datetime import timedelta, date, time
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from accounts.models import CustomUser
from organization.models import Department, Site
from recruitment.models import (
    RecruitmentJob, CandidateRegistrationLink, Candidate,
    CandidateEducation, CandidateExperience, CandidateSkill,
    CandidateDocument, JobApplication, ApplicationStatusHistory
)


class Command(BaseCommand):
    help = 'Seeds realistic recruitment data including job openings, shareable links, and candidate applications'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Recruitment & Candidate Portal demo data..."))

        hr_user = CustomUser.objects.filter(role='hr').first()
        if not hr_user:
            hr_user = CustomUser.objects.filter(is_superuser=True).first()

        dept_eng = Department.objects.filter(code='ENG').first()
        dept_prod = Department.objects.filter(code='PROD').first()
        dept_hr = Department.objects.filter(code='HR').first()
        site_blr = Site.objects.filter(code='BLR-HQ').first()
        site_hyd = Site.objects.filter(code='HYD-CAMPUS').first()

        today = timezone.localdate()

        # 1. Job Openings
        job_django, _ = RecruitmentJob.objects.get_or_create(
            title='Senior Full-Stack Django Developer',
            defaults={
                'department': dept_eng,
                'site': site_blr,
                'location': 'Bengaluru HQ & Hybrid',
                'employment_type': RecruitmentJob.EmploymentType.FULL_TIME,
                'vacancies': 3,
                'experience_required': '4-8 Years',
                'salary_range': '₹18,00,000 - ₹28,00,000 PA',
                'description': (
                    "We are seeking an experienced Senior Full-Stack Django Developer to architect, develop, "
                    "and scale enterprise web applications, real-time dashboards, and secure RBAC microservices. "
                    "You will work closely with engineering leads and product managers to drive technical excellence."
                ),
                'requirements': (
                    "• Strong expertise in Python 3, Django, Django REST Framework, and ORM query optimization.\n"
                    "• Experience with PostgreSQL database tuning, Redis caching, and Celery task queues.\n"
                    "• Proficiency in modern frontend technologies: HTML5, CSS3/Tailwind/Bootstrap, JavaScript (ES6+).\n"
                    "• Familiarity with Docker containerization, CI/CD pipelines, and AWS cloud deployment.\n"
                    "• Bachelor's or Master's degree in Computer Science, Software Engineering, or equivalent."
                ),
                'benefits': (
                    "• Comprehensive medical insurance covering family & parents.\n"
                    "• Flexible hybrid work policy (2 days WFH / week).\n"
                    "• Annual performance bonus and learning & certification stipend.\n"
                    "• Ergonomic home office setup allowance."
                ),
                'application_deadline': today + timedelta(days=35),
                'status': RecruitmentJob.Status.OPEN,
                'created_by': hr_user
            }
        )

        job_uiux, _ = RecruitmentJob.objects.get_or_create(
            title='Lead UI/UX Product Designer',
            defaults={
                'department': dept_prod,
                'site': site_blr,
                'location': 'Bengaluru HQ (Hybrid)',
                'employment_type': RecruitmentJob.EmploymentType.FULL_TIME,
                'vacancies': 2,
                'experience_required': '5-9 Years',
                'salary_range': '₹20,00,000 - ₹30,00,000 PA',
                'description': (
                    "Lead the UI/UX design lifecycle for enterprise SaaS applications, internal portals, and design systems. "
                    "Craft intuitive user workflows, interaction patterns, design tokens, and conduct user research."
                ),
                'requirements': (
                    "• Proven portfolio showcasing end-to-end B2B SaaS or enterprise web applications.\n"
                    "• Mastery of Figma, auto-layout, interactive prototypes, and design systems.\n"
                    "• Deep understanding of design accessibility (WCAG), responsive grids, and design tokens.\n"
                    "• Ability to translate complex domain workflows into elegant, friction-free interfaces."
                ),
                'benefits': (
                    "• Top-tier Apple MacBook Pro M3 Max hardware provided.\n"
                    "• Annual conference budget for Figma Config and UX design summits.\n"
                    "• Competitive health insurance and wellness perks."
                ),
                'application_deadline': today + timedelta(days=45),
                'status': RecruitmentJob.Status.OPEN,
                'created_by': hr_user
            }
        )

        job_trainee, _ = RecruitmentJob.objects.get_or_create(
            title='Graduate Trainee / Junior Python Engineer',
            defaults={
                'department': dept_eng,
                'site': site_blr,
                'location': 'Bengaluru HQ',
                'employment_type': RecruitmentJob.EmploymentType.INTERNSHIP,
                'vacancies': 5,
                'experience_required': 'Fresher / 0-1 Year',
                'salary_range': '₹4,50,000 - ₹6,50,000 PA',
                'description': (
                    "Fast-track your software engineering career with hands-on mentorship from senior architects. "
                    "Participate in building core modules, automated testing suites, and backend APIs."
                ),
                'requirements': (
                    "• B.Tech / B.E. / MCA / B.Sc in Computer Science (2025/2026 batch) with minimum 70% or 7.0 CGPA.\n"
                    "• Solid foundation in Python programming, OOP principles, and relational databases (SQL).\n"
                    "• Passion for problem-solving, clean code, and fast-paced learning."
                ),
                'benefits': (
                    "• Paid 6-month internship with pre-placement full-time offer conversion.\n"
                    "• Free catered meals and daily office shuttle."
                ),
                'application_deadline': today + timedelta(days=20),
                'status': RecruitmentJob.Status.OPEN,
                'created_by': hr_user
            }
        )

        # 2. Candidate Registration Links
        link1, _ = CandidateRegistrationLink.objects.get_or_create(
            token='linkedin-sr-django-2026',
            defaults={
                'job': job_django,
                'title': 'LinkedIn Talent Solutions Q4 Campaign',
                'expires_at': timezone.now() + timedelta(days=30),
                'max_applications': 100,
                'is_active': True,
                'views_count': 142,
                'created_by': hr_user
            }
        )

        link2, _ = CandidateRegistrationLink.objects.get_or_create(
            token='referral-django-blr',
            defaults={
                'job': job_django,
                'title': 'WhatsApp & Employee Referral Channel',
                'expires_at': timezone.now() + timedelta(days=45),
                'max_applications': 50,
                'is_active': True,
                'views_count': 68,
                'created_by': hr_user
            }
        )

        link3, _ = CandidateRegistrationLink.objects.get_or_create(
            token='dribbble-uiux-lead-2026',
            defaults={
                'job': job_uiux,
                'title': 'Dribbble & Design Communities Portal',
                'expires_at': timezone.now() + timedelta(days=40),
                'max_applications': 30,
                'is_active': True,
                'views_count': 95,
                'created_by': hr_user
            }
        )

        link4, _ = CandidateRegistrationLink.objects.get_or_create(
            token='campus-freshers-2026',
            defaults={
                'job': job_trainee,
                'title': 'College Campus Drive 2026',
                'expires_at': timezone.now() + timedelta(days=15),
                'max_applications': 150,
                'is_active': True,
                'views_count': 310,
                'created_by': hr_user
            }
        )

        # Inactive link for testing
        link_closed, _ = CandidateRegistrationLink.objects.get_or_create(
            token='expired-contractor-sample',
            defaults={
                'job': job_django,
                'title': 'Archived Contractor Drive (Closed)',
                'expires_at': timezone.now() - timedelta(days=5),
                'max_applications': 10,
                'is_active': False,
                'views_count': 22,
                'created_by': hr_user
            }
        )

        # 3. Candidates and Applications
        # Candidate 1: Priyabrata Nayak (Interview Scheduled)
        c1, _ = Candidate.objects.get_or_create(
            email='priyabrata.nayak.dev@gmail.com',
            defaults={
                'full_name': 'Priyabrata Nayak',
                'phone': '+91 98610 43210',
                'alt_phone': '+91 98610 43211',
                'date_of_birth': date(1996, 5, 14),
                'gender': 'MALE',
                'current_address': 'Plot 102, Saheed Nagar',
                'city': 'Bhubaneswar',
                'state': 'Odisha',
                'postal_code': '751007',
                'country': 'India',
            }
        )
        c1.full_name = 'Priyabrata Nayak'
        c1.phone = '+91 98610 43210'
        c1.current_address = 'Plot 102, Saheed Nagar'
        c1.city = 'Bhubaneswar'
        c1.state = 'Odisha'
        c1.postal_code = '751007'
        c1.save()

        CandidateEducation.objects.get_or_create(
            candidate=c1,
            defaults={
                'highest_qualification': 'B.Tech / B.E.',
                'degree_name': 'Bachelor of Technology in Computer Science & Engineering',
                'specialization': 'Computer Science & Distributed Systems',
                'institution': 'National Institute of Technology (NIT) Rourkela',
                'passing_year': 2018,
                'percentage_cgpa': '8.7 CGPA',
                'details_10th': 'BSE Odisha Board - 94.2% (2012)',
                'details_12th': 'CHSE Odisha Board - 96.0% (2014)',
                'additional_qualifications': 'Certified AWS Solutions Architect Associate (2024)'
            }
        )
        CandidateExperience.objects.get_or_create(
            candidate=c1,
            defaults={
                'experience_type': 'EXPERIENCED',
                'total_experience_years': 6,
                'total_experience_months': 2,
                'current_company': 'Infosys Limited (Bhubaneswar SEZ)',
                'current_designation': 'Senior Technology Specialist',
                'previous_company': 'Mindtree Consulting',
                'previous_experience_details': 'Full-stack development of financial billing portals using Django, PostgreSQL, and Angular.',
                'current_ctc': 1500000.00,
                'expected_ctc': 2200000.00,
                'notice_period_days': 30,
                'available_joining_date': today + timedelta(days=40)
            }
        )
        CandidateSkill.objects.get_or_create(
            candidate=c1,
            defaults={
                'technical_skills': 'Python 3, Django, Django REST Framework, PostgreSQL, Redis, Celery, Docker, Linux, Git, Unit Testing',
                'programming_languages': 'Python, JavaScript, SQL, Bash',
                'frameworks': 'Django, FastAPI, Bootstrap 5, Tailwind CSS',
                'certifications': 'AWS Solutions Architect Associate, Python Certified Professional',
                'projects': 'High-throughput enterprise HRMS API gateway handling 100k daily requests with sub-100ms response time.',
                'preferred_role': 'Senior Full-Stack Django Developer',
                'preferred_location': 'Bhubaneswar / Bengaluru',
                'portfolio_url': 'https://priyabratanayak.dev',
                'linkedin_url': 'https://linkedin.com/in/priyabrata-nayak-sample',
                'github_url': 'https://github.com/priyabratanayak-sample'
            }
        )

        app1 = JobApplication.objects.filter(candidate=c1, job=job_django).first()
        if not app1:
            app1 = JobApplication(
                candidate=c1,
                job=job_django,
                registration_link=link1,
                status=JobApplication.Status.INTERVIEW_SCHEDULED,
                rating=5,
                hr_notes=(
                    "Exceptional technical profile. Scored 95% on Django ORM optimization and Celery architectural screening. "
                    "Demonstrated deep understanding of multi-tenant database design and security headers."
                ),
                interview_date=today + timedelta(days=3),
                interview_time=time(14, 30),
                interview_mode='VIRTUAL',
                interview_location_link='https://meet.google.com/abc-defg-hij',
                interview_notes=(
                    "Round 2 Technical Deep Dive with VP of Engineering Debasish Mohapatra. "
                    "Agenda: System design discussion, database query tuning exercise, and architecture walkthrough."
                )
            )
            app1.resume.save('Priyabrata_Nayak_Resume.pdf', ContentFile(b"%PDF-1.4 Mock Senior Django Developer Resume Content"))
            app1.save()

            ApplicationStatusHistory.objects.create(
                application=app1,
                old_status='NONE',
                new_status=JobApplication.Status.SUBMITTED,
                changed_by=None,
                notes='Application received via LinkedIn Campaign link.'
            )
            ApplicationStatusHistory.objects.create(
                application=app1,
                old_status=JobApplication.Status.SUBMITTED,
                new_status=JobApplication.Status.SHORTLISTED,
                changed_by=hr_user,
                notes='Shortlisted based on 6 years relevant experience and NIT Rourkela background.'
            )
            ApplicationStatusHistory.objects.create(
                application=app1,
                old_status=JobApplication.Status.SHORTLISTED,
                new_status=JobApplication.Status.INTERVIEW_SCHEDULED,
                changed_by=hr_user,
                notes='Virtual Technical Round 2 scheduled for 2:30 PM with VP of Engineering.'
            )

        # Candidate 2: Chinmayee Mohanty (Shortlisted for UI/UX)
        c2, _ = Candidate.objects.get_or_create(
            email='chinmayee.mohanty.ux@gmail.com',
            defaults={
                'full_name': 'Chinmayee Mohanty',
                'phone': '+91 97781 32109',
                'alt_phone': '',
                'date_of_birth': date(1997, 8, 22),
                'gender': 'FEMALE',
                'current_address': 'Flat 204, Jayadev Vihar',
                'city': 'Bhubaneswar',
                'state': 'Odisha',
                'postal_code': '751013',
                'country': 'India',
            }
        )
        c2.full_name = 'Chinmayee Mohanty'
        c2.phone = '+91 97781 32109'
        c2.current_address = 'Flat 204, Jayadev Vihar'
        c2.city = 'Bhubaneswar'
        c2.state = 'Odisha'
        c2.postal_code = '751013'
        c2.save()

        CandidateEducation.objects.get_or_create(
            candidate=c2,
            defaults={
                'highest_qualification': 'Bachelor of Design (B.Des)',
                'degree_name': 'B.Des in Interaction & Communication Design',
                'specialization': 'Human-Computer Interaction (HCI)',
                'institution': 'National Institute of Design (NID) Ahmedabad',
                'passing_year': 2019,
                'percentage_cgpa': '8.9 CGPA',
                'details_10th': 'ICSE Board - 92.5%',
                'details_12th': 'ISC Board - 94.0%',
                'additional_qualifications': 'Nielsen Norman Group UX Master Certified'
            }
        )
        CandidateExperience.objects.get_or_create(
            candidate=c2,
            defaults={
                'experience_type': 'EXPERIENCED',
                'total_experience_years': 5,
                'total_experience_months': 6,
                'current_company': 'Swiggy',
                'current_designation': 'Senior Product Designer',
                'previous_company': 'Razorpay',
                'previous_experience_details': 'Led design for merchant analytics dashboards, checkout flow optimizations, and design system tokens.',
                'current_ctc': 1900000.00,
                'expected_ctc': 2600000.00,
                'notice_period_days': 45,
                'available_joining_date': today + timedelta(days=50)
            }
        )
        CandidateSkill.objects.get_or_create(
            candidate=c2,
            defaults={
                'technical_skills': 'Figma, Design Systems, Wireframing, High-fidelity Prototyping, Usability Testing, User Journey Mapping, Design Tokens',
                'programming_languages': 'HTML5, CSS3, Basic React',
                'frameworks': 'Tailwind CSS, Bootstrap, Material 3',
                'certifications': 'NN/g UX Master Certification, Interaction Design Foundation',
                'projects': 'Revamped merchant analytics portal resulting in 34% increase in dashboard engagement and 18% reduction in support tickets.',
                'preferred_role': 'Lead UI/UX Product Designer',
                'preferred_location': 'Bhubaneswar / Bengaluru',
                'portfolio_url': 'https://chinmayeedesigns.work',
                'linkedin_url': 'https://linkedin.com/in/chinmayee-mohanty-sample',
                'github_url': ''
            }
        )

        app2 = JobApplication.objects.filter(candidate=c2, job=job_uiux).first()
        if not app2:
            app2 = JobApplication(
                candidate=c2,
                job=job_uiux,
                registration_link=link3,
                status=JobApplication.Status.SHORTLISTED,
                rating=4,
                hr_notes="World-class portfolio on enterprise design tokens and dashboard analytics. Highly articulate design rationale. Moving to portfolio presentation stage."
            )
            app2.resume.save('Chinmayee_Mohanty_Resume.pdf', ContentFile(b"%PDF-1.4 Mock Lead UI/UX Designer Resume Content"))
            app2.save()

            ApplicationStatusHistory.objects.create(
                application=app2,
                old_status='NONE',
                new_status=JobApplication.Status.SUBMITTED,
                changed_by=None,
                notes='Application received via Dribbble & Design link.'
            )
            ApplicationStatusHistory.objects.create(
                application=app2,
                old_status=JobApplication.Status.SUBMITTED,
                new_status=JobApplication.Status.SHORTLISTED,
                changed_by=hr_user,
                notes='Shortlisted based on NID credentials and Razorpay/Swiggy product portfolio.'
            )

        # Candidate 3: Tapas Kumar Behera (Graduate Fresher)
        c3, _ = Candidate.objects.get_or_create(
            email='tapas.behera.2025@gmail.com',
            defaults={
                'full_name': 'Tapas Kumar Behera',
                'phone': '+91 94371 21098',
                'alt_phone': '',
                'date_of_birth': date(2003, 11, 8),
                'gender': 'MALE',
                'current_address': 'Room 304, Boys Hostel 2, OUTR Campus, Ghatikia',
                'city': 'Bhubaneswar',
                'state': 'Odisha',
                'postal_code': '751003',
                'country': 'India',
            }
        )
        c3.full_name = 'Tapas Kumar Behera'
        c3.phone = '+91 94371 21098'
        c3.current_address = 'Room 304, Boys Hostel 2, OUTR Campus, Ghatikia'
        c3.city = 'Bhubaneswar'
        c3.state = 'Odisha'
        c3.postal_code = '751003'
        c3.save()

        CandidateEducation.objects.get_or_create(
            candidate=c3,
            defaults={
                'highest_qualification': 'B.Tech / B.E.',
                'degree_name': 'B.Tech in Computer Science & Engineering',
                'specialization': 'Software Engineering',
                'institution': 'Odisha University of Technology and Research (OUTR), Bhubaneswar',
                'passing_year': 2025,
                'percentage_cgpa': '8.8 CGPA',
                'details_10th': 'BSE Odisha - 91.0%',
                'details_12th': 'CHSE Odisha - 93.5%',
                'additional_qualifications': 'LeetCode 400+ problems solved, HackerRank 5-star Python'
            }
        )
        CandidateExperience.objects.get_or_create(
            candidate=c3,
            defaults={
                'experience_type': 'FRESHER',
                'total_experience_years': 0,
                'total_experience_months': 0,
                'current_company': '',
                'current_designation': '',
                'previous_company': '',
                'previous_experience_details': '',
                'current_ctc': None,
                'expected_ctc': 550000.00,
                'notice_period_days': 0,
                'available_joining_date': today + timedelta(days=15)
            }
        )
        CandidateSkill.objects.get_or_create(
            candidate=c3,
            defaults={
                'technical_skills': 'Python, Django, SQLite, PostgreSQL, HTML5, CSS3, JavaScript, Git, Linux',
                'programming_languages': 'Python, C++, SQL',
                'frameworks': 'Django, Bootstrap 5',
                'certifications': 'Python for Everybody Specialization (Coursera)',
                'projects': 'Built student attendance & library management system with Django and role-based permissions.',
                'preferred_role': 'Graduate Trainee / Junior Python Developer',
                'preferred_location': 'Bhubaneswar / Bengaluru',
                'portfolio_url': 'https://github.com/tapasbehera-sample',
                'linkedin_url': 'https://linkedin.com/in/tapas-behera-sample',
                'github_url': 'https://github.com/tapasbehera-sample'
            }
        )

        app3 = JobApplication.objects.filter(candidate=c3, job=job_trainee).first()
        if not app3:
            app3 = JobApplication(
                candidate=c3,
                job=job_trainee,
                registration_link=link4,
                status=JobApplication.Status.UNDER_REVIEW,
                rating=4,
                hr_notes="Strong fresher profile with high CGPA and hands-on Django projects. Good potential for the engineering graduate cohort."
            )
            app3.resume.save('Tapas_Behera_Fresher_Resume.pdf', ContentFile(b"%PDF-1.4 Mock Graduate Trainee Resume Content"))
            app3.save()

            ApplicationStatusHistory.objects.create(
                application=app3,
                old_status='NONE',
                new_status=JobApplication.Status.SUBMITTED,
                changed_by=None,
                notes='Application received via Campus Drive link.'
            )
            ApplicationStatusHistory.objects.create(
                application=app3,
                old_status=JobApplication.Status.SUBMITTED,
                new_status=JobApplication.Status.UNDER_REVIEW,
                changed_by=hr_user,
                notes='Profile queued for screening test evaluation.'
            )

        # Candidate 4: Lipsa Pradhan (Submitted, awaiting initial HR review)
        c4, _ = Candidate.objects.get_or_create(
            email='lipsa.pradhan.backend@gmail.com',
            defaults={
                'full_name': 'Lipsa Pradhan',
                'phone': '+91 99370 10987',
                'alt_phone': '',
                'date_of_birth': date(1998, 3, 19),
                'gender': 'FEMALE',
                'current_address': 'Quarter 12, CDA Sector 9',
                'city': 'Cuttack',
                'state': 'Odisha',
                'postal_code': '753014',
                'country': 'India',
            }
        )
        c4.full_name = 'Lipsa Pradhan'
        c4.phone = '+91 99370 10987'
        c4.current_address = 'Quarter 12, CDA Sector 9'
        c4.city = 'Cuttack'
        c4.state = 'Odisha'
        c4.postal_code = '753014'
        c4.save()

        CandidateEducation.objects.get_or_create(
            candidate=c4,
            defaults={
                'highest_qualification': 'MCA (Master of Computer Applications)',
                'degree_name': 'Master of Computer Applications',
                'specialization': 'Cloud Computing & Database Systems',
                'institution': 'Silicon Institute of Technology, Bhubaneswar',
                'passing_year': 2021,
                'percentage_cgpa': '8.4 CGPA',
                'details_10th': 'BSE Odisha Board - 89.0%',
                'details_12th': 'CHSE Odisha Board - 91.2%'
            }
        )
        CandidateExperience.objects.get_or_create(
            candidate=c4,
            defaults={
                'experience_type': 'EXPERIENCED',
                'total_experience_years': 3,
                'total_experience_months': 4,
                'current_company': 'Tata Consultancy Services (TCS Bhubaneswar)',
                'current_designation': 'Systems Engineer (Python Developer)',
                'previous_company': '',
                'previous_experience_details': 'Developed RESTful services with Django REST framework and integrated third-party payment gateways.',
                'current_ctc': 900000.00,
                'expected_ctc': 1400000.00,
                'notice_period_days': 60,
                'available_joining_date': today + timedelta(days=65)
            }
        )
        CandidateSkill.objects.get_or_create(
            candidate=c4,
            defaults={
                'technical_skills': 'Python, Django REST Framework, MySQL, Git, Postman, Jenkins',
                'programming_languages': 'Python, SQL',
                'frameworks': 'Django, DRF',
                'certifications': 'Oracle Certified Associate Python',
                'projects': 'Automated reporting pipeline for retail analytics client.',
                'preferred_role': 'Python Developer',
                'preferred_location': 'Bhubaneswar',
                'portfolio_url': '',
                'linkedin_url': 'https://linkedin.com/in/lipsa-pradhan-sample',
                'github_url': 'https://github.com/lipsapradhan-sample'
            }
        )

        app4 = JobApplication.objects.filter(candidate=c4, job=job_django).first()
        if not app4:
            app4 = JobApplication(
                candidate=c4,
                job=job_django,
                registration_link=link2,
                status=JobApplication.Status.SUBMITTED,
                rating=0,
                hr_notes=""
            )
            app4.resume.save('Lipsa_Pradhan_Resume.pdf', ContentFile(b"%PDF-1.4 Mock Python Developer Resume Content"))
            app4.save()

            ApplicationStatusHistory.objects.create(
                application=app4,
                old_status='NONE',
                new_status=JobApplication.Status.SUBMITTED,
                changed_by=None,
                notes='Application received via WhatsApp & Referral channel.'
            )

        self.stdout.write(self.style.SUCCESS("Recruitment demo data seeded successfully!"))
        self.stdout.write(self.style.SUCCESS(f"""
Generated Shareable Registration Links:
  1. Senior Full-Stack Django Dev (LinkedIn Campaign):
     Token: {link1.token}
     Public Registration URL: /candidate/register/{link1.token}/
  2. Senior Full-Stack Django Dev (WhatsApp / Referral):
     Token: {link2.token}
     Public Registration URL: /candidate/register/{link2.token}/
  3. Lead UI/UX Product Designer:
     Token: {link3.token}
     Public Registration URL: /candidate/register/{link3.token}/
  4. Graduate Trainee (Campus Drive):
     Token: {link4.token}
     Public Registration URL: /candidate/register/{link4.token}/

Trackable Sample Applications:
  - {app1.application_id} (Priyabrata Nayak - Interview Scheduled)
    URL: /candidate/track/{app1.application_id}/
  - {app2.application_id} (Chinmayee Mohanty - Shortlisted)
    URL: /candidate/track/{app2.application_id}/
  - {app3.application_id} (Tapas Kumar Behera - Under Review)
    URL: /candidate/track/{app3.application_id}/
  - {app4.application_id} (Lipsa Pradhan - Submitted)
    URL: /candidate/track/{app4.application_id}/
"""))

