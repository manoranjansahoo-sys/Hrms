from django.db import models
from django.conf import settings
from organization.models import Department, Designation, Site


class EmployeeProfile(models.Model):
    class EmploymentType(models.TextChoices):
        FULL_TIME = 'FULL_TIME', 'Full Time'
        PART_TIME = 'PART_TIME', 'Part Time'
        CONTRACT = 'CONTRACT', 'Contract'
        INTERN = 'INTERN', 'Intern'

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        ON_NOTICE = 'ON_NOTICE', 'On Notice'
        RESIGNED = 'RESIGNED', 'Resigned'
        TERMINATED = 'TERMINATED', 'Terminated'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )
    emp_id = models.CharField(max_length=20, unique=True, db_index=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    designation = models.ForeignKey(
        Designation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    site = models.ForeignKey(
        Site,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    reporting_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reportees'
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME
    )
    joining_date = models.DateField()
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=20,
        choices=[
            ('MALE', 'Male'),
            ('FEMALE', 'Female'),
            ('OTHER', 'Other'),
            ('UNDISCLOSED', 'Prefer not to say'),
        ],
        default='MALE'
    )
    marital_status = models.CharField(
        max_length=20,
        choices=[
            ('SINGLE', 'Single'),
            ('MARRIED', 'Married'),
            ('DIVORCED', 'Divorced'),
            ('WIDOWED', 'Widowed'),
        ],
        default='SINGLE'
    )
    blood_group = models.CharField(max_length=10, blank=True)
    personal_email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_relation = models.CharField(max_length=50, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    # Bank and sensitive info - strict role-based access!
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=30, blank=True)
    pan_number = models.CharField(max_length=30, blank=True)
    uan_number = models.CharField(max_length=30, blank=True)

    education_details = models.TextField(blank=True, help_text="Degrees, universities, graduating years")
    experience_summary = models.TextField(blank=True, help_text="Prior work experience overview")

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    show_birthday_publicly = models.BooleanField(
        default=True,
        help_text="Display birthday in portal calendar and celebration card"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['emp_id']

    def __str__(self):
        return f"{self.emp_id} - {self.user.get_full_name() or self.user.username}"

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username

    @property
    def email(self):
        return self.user.email

    @property
    def phone(self):
        return self.user.phone

    @property
    def masked_account_number(self):
        if not self.bank_account_number or len(self.bank_account_number) < 4:
            return "••••••••"
        return "••••" + self.bank_account_number[-4:]


class EmployeeDocument(models.Model):
    DOC_TYPES = [
        ('ID_PROOF', 'National ID / Passport / Driving License'),
        ('RESUME', 'Resume / Curriculum Vitae'),
        ('OFFER_LETTER', 'Offer / Appointment Letter'),
        ('CERTIFICATE', 'Degree / Educational Certificate'),
        ('TAX_DOCUMENT', 'Tax Exemption / Declaration Form'),
        ('OTHER', 'Other Verified Document'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=30, choices=DOC_TYPES, default='OTHER')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='employee_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.employee.emp_id} - {self.title}"


class ProfileCorrectionRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending HR Review'),
        ('APPROVED', 'Approved & Applied'),
        ('REJECTED', 'Rejected'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='correction_requests')
    field_name = models.CharField(max_length=100, help_text="Name of field requested to update")
    current_value = models.TextField()
    proposed_value = models.TextField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_profile_corrections'
    )
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Correction for {self.employee.emp_id}: {self.field_name} ({self.status})"
