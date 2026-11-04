import secrets
from django.db import models
from django.conf import settings
from django.utils import timezone
from organization.models import Department, Site


class RecruitmentJob(models.Model):
    class EmploymentType(models.TextChoices):
        FULL_TIME = 'FULL_TIME', 'Full-time'
        PART_TIME = 'PART_TIME', 'Part-time'
        INTERNSHIP = 'INTERNSHIP', 'Internship'
        CONTRACT = 'CONTRACT', 'Contract'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        OPEN = 'OPEN', 'Open / Active'
        ON_HOLD = 'ON_HOLD', 'On Hold'
        CLOSED = 'CLOSED', 'Closed'

    title = models.CharField(max_length=200, help_text="Job Opening Title")
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recruitment_jobs'
    )
    site = models.ForeignKey(
        Site,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='recruitment_jobs'
    )
    location = models.CharField(max_length=150, default='Bengaluru HQ & Hybrid')
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME
    )
    vacancies = models.PositiveIntegerField(default=1)
    experience_required = models.CharField(max_length=50, default='2-5 Years')
    salary_range = models.CharField(max_length=100, blank=True, help_text="e.g. ₹12,00,000 - ₹18,00,000 PA")
    description = models.TextField(help_text="Detailed overview and role objectives")
    requirements = models.TextField(help_text="Key responsibilities and qualifications required")
    benefits = models.TextField(blank=True, help_text="Corporate perks, comprehensive health coverage, flexible hours")
    application_deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_jobs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        dept_code = self.department.code if self.department else 'GEN'
        return f"{self.title} ({dept_code} - {self.get_employment_type_display()})"

    @property
    def is_active(self):
        if self.status != self.Status.OPEN:
            return False
        if self.application_deadline and self.application_deadline < timezone.localdate():
            return False
        return True

    @property
    def total_applications_count(self):
        return self.applications.count()


class CandidateRegistrationLink(models.Model):
    job = models.ForeignKey(
        RecruitmentJob,
        on_delete=models.CASCADE,
        related_name='registration_links'
    )
    token = models.CharField(max_length=64, unique=True, db_index=True)
    title = models.CharField(
        max_length=200,
        help_text="Campaign name or channel (e.g. 'LinkedIn Q4 Campaign', 'Campus Drive 2026', 'Referral Link')"
    )
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Optional expiration date/time")
    max_applications = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional maximum number of applications before link automatically closes"
    )
    is_active = models.BooleanField(default=True)
    views_count = models.PositiveIntegerField(default=0)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_candidate_links'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.token:
            # Generate collision-free secure URL-safe token
            for _ in range(10):
                new_token = secrets.token_urlsafe(16)
                if not CandidateRegistrationLink.objects.filter(token=new_token).exists():
                    self.token = new_token
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.job.title} - {self.title} [{self.token[:8]}...]"

    @property
    def applications_count(self):
        return self.applications.count()

    @property
    def is_expired(self):
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False

    @property
    def is_limit_reached(self):
        if self.max_applications and self.applications_count >= self.max_applications:
            return True
        return False

    @property
    def is_valid(self):
        if not self.is_active:
            return False
        if not self.job.is_active:
            return False
        if self.is_expired:
            return False
        if self.is_limit_reached:
            return False
        return True

    @property
    def status_label(self):
        if not self.is_active:
            return 'Closed'
        if self.is_expired:
            return 'Expired'
        if self.is_limit_reached:
            return 'Limit Reached'
        return 'Active'


class Candidate(models.Model):
    GENDER_CHOICES = [
        ('MALE', 'Male'),
        ('FEMALE', 'Female'),
        ('OTHER', 'Other'),
        ('UNDISCLOSED', 'Prefer not to say'),
    ]

    full_name = models.CharField(max_length=150)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=20)
    alt_phone = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='UNDISCLOSED')
    photo = models.ImageField(upload_to='candidates/photos/', blank=True, null=True)

    current_address = models.TextField(blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, default='')
    postal_code = models.CharField(max_length=20, blank=True, default='')
    country = models.CharField(max_length=100, default='India')

    # Full Onboarding & Statutory Details (Filled after qualifying interview)
    father_name = models.CharField(max_length=150, blank=True)
    blood_group = models.CharField(max_length=10, blank=True)
    marital_status = models.CharField(max_length=20, blank=True)
    permanent_address = models.TextField(blank=True)
    emergency_contact_name = models.CharField(max_length=150, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)
    pan_number = models.CharField(max_length=20, blank=True)
    aadhaar_number = models.CharField(max_length=20, blank=True)
    bank_name = models.CharField(max_length=150, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    bank_ifsc_code = models.CharField(max_length=20, blank=True)
    bank_branch = models.CharField(max_length=150, blank=True)
    pf_uan_number = models.CharField(max_length=30, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.email})"

    def get_photo_url(self):
        if self.photo and hasattr(self.photo, 'url'):
            return self.photo.url
        name_parts = self.full_name.split()
        first = name_parts[0] if name_parts else 'User'
        last = name_parts[-1] if len(name_parts) > 1 else ''
        return f"https://ui-avatars.com/api/?name={first}+{last}&background=2E7D32&color=fff&size=128"


class CandidateEducation(models.Model):
    candidate = models.OneToOneField(
        Candidate,
        on_delete=models.CASCADE,
        related_name='education'
    )
    highest_qualification = models.CharField(
        max_length=100,
        help_text="e.g. B.Tech / B.E., M.Tech, MCA, MBA, B.Sc, BCA, Diploma"
    )
    degree_name = models.CharField(max_length=150, blank=True, help_text="Degree / Course Title")
    specialization = models.CharField(max_length=150, blank=True, help_text="Major / Stream")
    institution = models.CharField(max_length=200, blank=True, help_text="College / University Name")
    passing_year = models.PositiveIntegerField(null=True, blank=True, help_text="Graduation Year")
    percentage_cgpa = models.CharField(max_length=20, blank=True, help_text="e.g. 8.4 CGPA or 82%")

    details_10th = models.CharField(max_length=150, blank=True, help_text="10th Board, Year & Score")
    details_12th = models.CharField(max_length=150, blank=True, help_text="12th / Diploma Board, Year & Score")
    additional_qualifications = models.TextField(blank=True, help_text="Postgraduate diplomas or other academic honors")

    def __str__(self):
        return f"{self.highest_qualification} - {self.institution}"


class CandidateExperience(models.Model):
    EXPERIENCE_TYPE_CHOICES = [
        ('FRESHER', 'Fresher / Entry Level'),
        ('EXPERIENCED', 'Experienced Professional'),
    ]

    candidate = models.OneToOneField(
        Candidate,
        on_delete=models.CASCADE,
        related_name='experience'
    )
    experience_type = models.CharField(
        max_length=20,
        choices=EXPERIENCE_TYPE_CHOICES,
        default='EXPERIENCED'
    )
    total_experience_years = models.PositiveIntegerField(default=0)
    total_experience_months = models.PositiveIntegerField(default=0)
    current_company = models.CharField(max_length=150, blank=True)
    current_designation = models.CharField(max_length=150, blank=True)
    previous_company = models.CharField(max_length=150, blank=True)
    previous_experience_details = models.TextField(blank=True, help_text="Summary of prior companies and roles")
    current_ctc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual Current CTC (INR)"
    )
    expected_ctc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual Expected CTC (INR)"
    )
    notice_period_days = models.PositiveIntegerField(default=30, help_text="Notice period in days")
    available_joining_date = models.DateField(null=True, blank=True)

    def __str__(self):
        if self.experience_type == 'FRESHER':
            return "Fresher"
        return f"{self.total_experience_years}y {self.total_experience_months}m at {self.current_company or 'Previous'}"


class CandidateSkill(models.Model):
    candidate = models.OneToOneField(
        Candidate,
        on_delete=models.CASCADE,
        related_name='skills'
    )
    technical_skills = models.TextField(help_text="Primary technical skills (e.g. Python, Django, PostgreSQL, Docker)")
    programming_languages = models.CharField(max_length=255, blank=True, help_text="Languages known")
    frameworks = models.CharField(max_length=255, blank=True, help_text="Libraries / Frameworks")
    certifications = models.TextField(blank=True, help_text="Industry certifications, AWS, PMP, etc.")
    projects = models.TextField(blank=True, help_text="Key projects delivered and responsibilities")
    preferred_role = models.CharField(max_length=150, blank=True)
    preferred_location = models.CharField(max_length=150, blank=True)
    portfolio_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)

    def __str__(self):
        return f"Skills for {self.candidate.full_name}"


class CandidateDocument(models.Model):
    DOC_TYPES = [
        ('RESUME', 'Resume / Curriculum Vitae'),
        ('PHOTO', 'Profile Photograph'),
        ('CERTIFICATE', 'Educational Degree / Certificate'),
        ('EXPERIENCE_LETTER', 'Experience / Relieving Letter'),
        ('PAYSLIP', 'Recent Payslip / Form 16'),
        ('PAN_CARD', 'PAN Card Copy'),
        ('AADHAAR_CARD', 'Aadhaar / National ID Proof'),
        ('BANK_PROOF', 'Cancelled Cheque / Bank Passbook'),
        ('OTHER', 'Other Supporting Document'),
    ]

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    doc_type = models.CharField(max_length=30, choices=DOC_TYPES, default='OTHER')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='candidates/documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.candidate.full_name} - {self.title}"


class JobApplication(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        SHORTLISTED = 'SHORTLISTED', 'Shortlisted'
        INTERVIEW_SCHEDULED = 'INTERVIEW_SCHEDULED', 'Interview Scheduled'
        SELECTED = 'SELECTED', 'Interview Qualified / Selected'
        ONBOARDING_COMPLETED = 'ONBOARDING_COMPLETED', 'Onboarding Details Submitted'
        HIRED = 'HIRED', 'Hired / Joined'
        REJECTED = 'REJECTED', 'Rejected'
        ON_HOLD = 'ON_HOLD', 'On Hold'

    application_id = models.CharField(max_length=30, unique=True, db_index=True)
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    job = models.ForeignKey(
        RecruitmentJob,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    registration_link = models.ForeignKey(
        CandidateRegistrationLink,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications'
    )
    resume = models.FileField(upload_to='candidates/resumes/')
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.SUBMITTED)
    is_onboarding_completed = models.BooleanField(default=False)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)

    # Internal HR notes (Confidential - never exposed to candidate!)
    hr_notes = models.TextField(blank=True, help_text="Confidential internal HR evaluation notes")
    rating = models.PositiveSmallIntegerField(default=0, help_text="HR evaluation rating 1-5")

    # Interview scheduling details
    interview_date = models.DateField(null=True, blank=True)
    interview_time = models.TimeField(null=True, blank=True)
    interview_mode = models.CharField(
        max_length=30,
        choices=[
            ('VIRTUAL', 'Virtual (Google Meet / Microsoft Teams)'),
            ('IN_PERSON', 'In-Person (Office Campus)'),
            ('TELEPHONIC', 'Telephonic Round'),
        ],
        default='VIRTUAL',
        blank=True
    )
    interview_location_link = models.CharField(
        max_length=255,
        blank=True,
        help_text="Virtual meeting URL or office conference room venue"
    )
    interview_notes = models.TextField(blank=True, help_text="Candidate-facing interview guidelines or agenda")

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']
        unique_together = ('candidate', 'job')

    def save(self, *args, **kwargs):
        if not self.application_id:
            # Generate compact unique 5-digit application ID e.g. APP-10369
            rand_code = secrets.randbelow(90000) + 10000
            self.application_id = f"APP-{rand_code}"
            # Ensure uniqueness
            while JobApplication.objects.filter(application_id=self.application_id).exists():
                rand_code = secrets.randbelow(90000) + 10000
                self.application_id = f"APP-{rand_code}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.application_id} - {self.candidate.full_name} ({self.job.title})"

    @property
    def is_qualified(self):
        return self.status in [self.Status.SELECTED, self.Status.ONBOARDING_COMPLETED, self.Status.HIRED]


class ApplicationStatusHistory(models.Model):
    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    old_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    notes = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']

    def __str__(self):
        return f"{self.application.application_id}: {self.old_status} -> {self.new_status} at {self.changed_at}"
