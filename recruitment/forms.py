import os
import re
from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from organization.models import Department, Site
from recruitment.models import (
    RecruitmentJob, CandidateRegistrationLink, JobApplication,
    Candidate, CandidateEducation, CandidateExperience, CandidateSkill,
    CandidateDocument
)


class JobOpeningForm(forms.ModelForm):
    class Meta:
        model = RecruitmentJob
        fields = [
            'title', 'department', 'site', 'location',
            'employment_type', 'vacancies', 'experience_required',
            'salary_range', 'application_deadline', 'status',
            'description', 'requirements', 'benefits'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Senior Full-Stack Django Developer'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'site': forms.Select(attrs={'class': 'form-select'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Bengaluru HQ & Hybrid'}),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'vacancies': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'experience_required': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 3-6 Years'}),
            'salary_range': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ₹15,00,000 - ₹22,00,000 PA'}),
            'application_deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Comprehensive role description...'}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Key responsibilities and qualifications...'}),
            'benefits': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Perks, health insurance, learning budget...'}),
        }


class CandidateRegistrationLinkForm(forms.ModelForm):
    class Meta:
        model = CandidateRegistrationLink
        fields = ['job', 'title', 'expires_at', 'max_applications', 'is_active']
        widgets = {
            'job': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "e.g. 'LinkedIn Talent Drive', 'Campus Referral Link'"}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'max_applications': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 50 (Leave blank for unlimited)', 'min': 1}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input', 'checked': True}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['job'].queryset = RecruitmentJob.objects.filter(status=RecruitmentJob.Status.OPEN)


# -------------------------------------------------------------
# FILE VALIDATORS
# -------------------------------------------------------------

def validate_resume_file(value):
    """Validates that uploaded resume is PDF or Word doc and <= 10MB."""
    if not value:
        raise ValidationError("Please upload your resume file.")

    filename = getattr(value, 'name', '')
    ext = os.path.splitext(filename)[1].strip().lower()
    allowed_exts = ['.pdf', '.docx', '.doc']

    if ext not in allowed_exts:
        raise ValidationError(
            f"Invalid file extension '{ext or 'unknown'}'. Please upload your resume in PDF (.pdf) or Word (.docx / .doc) format."
        )

    if hasattr(value, 'size') and value.size > 10 * 1024 * 1024:
        raise ValidationError(
            f"Resume file size exceeds the 10MB limit ({round(value.size / (1024*1024), 1)}MB uploaded). Please upload a compressed document."
        )


def validate_document_file(value):
    """Validates verification document files (PDF or images <= 5MB)."""
    if not value:
        return
    filename = getattr(value, 'name', '')
    ext = os.path.splitext(filename)[1].strip().lower()
    allowed_exts = ['.pdf', '.docx', '.doc', '.jpg', '.jpeg', '.png']
    if ext not in allowed_exts:
        raise ValidationError("Only PDF, Word, or image (JPG, PNG) files are allowed.")
    if hasattr(value, 'size') and value.size > 5 * 1024 * 1024:
        raise ValidationError("File size exceeds 5MB limit.")


# -------------------------------------------------------------
# STAGE 1: PRE-INTERVIEW CANDIDATE REGISTRATION FORM (LESS DATA)
# -------------------------------------------------------------

class PreInterviewApplicationForm(forms.Form):
    """
    Streamlined 1st Stage Application Form (Google Form Style).
    Supports choosing any active position from Master Data, or pre-selected job from link.
    Minimal, high-signal data needed specifically for interview screening.
    Fast to fill in 1-2 minutes with guaranteed, forgiving resume upload.
    """
    # 0. Position / Role Selection (Master Data)
    job = forms.ModelChoiceField(
        queryset=RecruitmentJob.objects.filter(status=RecruitmentJob.Status.OPEN),
        empty_label="-- Select Position / Job Role --",
        label="Position / Role You Are Applying For",
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-lg',
            'id': 'positionSelect'
        })
    )

    # 1. Personal & Contact
    full_name = forms.CharField(
        max_length=150,
        label="Full Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name', 'required': True})
    )
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com', 'required': True})
    )
    phone = forms.CharField(
        max_length=20,
        label="Mobile Phone Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_phone',
            'placeholder': '10-digit mobile number',
            'maxlength': '10',
            'inputmode': 'numeric',
            'pattern': '[6-9][0-9]{9}',
            'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);",
            'required': True
        })
    )
    alt_phone = forms.CharField(
        max_length=20,
        required=False,
        label="Alternative Phone Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_alt_phone',
            'placeholder': '10-digit alternative number',
            'maxlength': '10',
            'inputmode': 'numeric',
            'pattern': '[6-9][0-9]{9}',
            'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);"
        })
    )
    current_address = forms.CharField(
        label="Current Residential Address (House No, Building, Street)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_current_address',
            'placeholder': 'House/Flat No., Street, Locality',
            'required': True
        })
    )
    city = forms.CharField(
        max_length=100,
        label="City",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_city',
            'placeholder': 'e.g. Bengaluru',
            'required': True
        })
    )
    state = forms.CharField(
        max_length=100,
        label="State / Province",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_state',
            'placeholder': 'e.g. Karnataka',
            'required': True
        })
    )
    postal_code = forms.CharField(
        max_length=20,
        label="PIN / Postal Code",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_postal_code',
            'placeholder': 'e.g. 560103',
            'required': True,
            'maxlength': '10',
            'inputmode': 'numeric',
            'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 6);"
        })
    )
    country = forms.CharField(
        max_length=100,
        initial='India',
        label="Country / Nationality",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_country',
            'placeholder': 'India',
            'required': True
        })
    )

    # 2. Highest Qualification Summary
    highest_qualification = forms.CharField(
        max_length=100,
        label="Highest Qualification",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. B.Tech, MCA, MBA',
            'required': True
        })
    )
    institution = forms.CharField(
        max_length=200,
        required=False,
        label="College / University Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'College / University'})
    )

    # 3. Work Experience Summary
    experience_type = forms.ChoiceField(
        choices=CandidateExperience.EXPERIENCE_TYPE_CHOICES,
        initial='EXPERIENCED',
        label="Experience Level",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'experienceTypeSelect'})
    )
    total_experience_years = forms.IntegerField(
        min_value=0,
        initial=0,
        required=False,
        label="Total Experience (Years)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'expYears', 'placeholder': 'Years (e.g. 3)'})
    )
    current_company = forms.CharField(
        max_length=150,
        required=False,
        label="Current Employer / Company",
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'currentCompanyInput', 'placeholder': 'Company Name'})
    )
    current_designation = forms.CharField(
        max_length=150,
        required=False,
        label="Current Job Title",
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'currentDesigInput', 'placeholder': 'Job Title'})
    )
    notice_period_days = forms.IntegerField(
        min_value=0,
        initial=30,
        required=False,
        label="Notice Period (Days)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '30'})
    )
    expected_ctc = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        label="Expected Annual CTC (₹)",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Expected CTC (₹)'})
    )

    # 4. Key Skills
    technical_skills = forms.CharField(
        label="Key Skills & Technologies",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'e.g. Python, Django, SQL, JavaScript',
            'required': True
        })
    )

    # 5. Resume Upload (Bulletproof)
    resume = forms.FileField(
        label="Resume / CV File",
        validators=[validate_resume_file],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.docx,.doc', 'required': True})
    )

    # 6. Optional Links
    linkedin_url = forms.URLField(
        required=False,
        label="LinkedIn Profile URL",
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/in/profile'})
    )
    portfolio_url = forms.URLField(
        required=False,
        label="GitHub / Portfolio URL",
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://github.com/profile'})
    )

    def __init__(self, *args, default_job=None, selected_job=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_job = default_job or selected_job
        self.fields['job'].queryset = RecruitmentJob.objects.filter(
            status=RecruitmentJob.Status.OPEN
        ).select_related('department')
        if self.default_job:
            job_id = self.default_job.id if hasattr(self.default_job, 'id') else self.default_job
            self.fields['job'].initial = job_id

    def clean(self):
        cleaned_data = super().clean()
        job = cleaned_data.get('job')
        if not job and hasattr(self, 'default_job') and self.default_job:
            cleaned_data['job'] = self.default_job
            job = self.default_job
        if not job:
            self.add_error('job', "Please select the position you are applying for from the dropdown.")
        return cleaned_data

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        digits = re.sub(r'\D', '', phone)
        if digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]
        elif digits.startswith('0') and len(digits) == 11:
            digits = digits[1:]
        if not re.match(r'^[6-9]\d{9}$', digits):
            raise ValidationError("Mobile phone number must be exactly 10 digits starting with 6, 7, 8, or 9 (no letters or negative numbers).")
        return digits

    def clean_alt_phone(self):
        return self.cleaned_data.get('alt_phone', '').strip()

    def clean_total_experience_years(self):
        exp_type = self.cleaned_data.get('experience_type')
        years = self.cleaned_data.get('total_experience_years')
        if exp_type == 'FRESHER':
            return 0
        return years or 0


# Backward compatibility alias
CandidateRegistrationStepForm = PreInterviewApplicationForm


# -------------------------------------------------------------
# LINKEDIN & WEBSITE FAST-APPLY APPLICATION FORM (WITH GOOGLE AUTH)
# -------------------------------------------------------------

class QuickSocialApplicationForm(forms.Form):
    """
    LinkedIn & Website Direct Fast-Apply Form with Google Sign-In Verification.
    Contains: Position, Name, Email ID, Phone No, Alternative Phone No, and Resume Upload.
    """
    job = forms.ModelChoiceField(
        queryset=RecruitmentJob.objects.filter(status=RecruitmentJob.Status.OPEN),
        empty_label="-- Select Position / Job Role --",
        label="Position / Role You Are Applying For",
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'positionSelect'
        })
    )
    full_name = forms.CharField(
        max_length=150,
        label="Full Name",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_full_name',
            'placeholder': 'Full Name',
            'required': True
        })
    )
    email = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'id': 'id_email',
            'placeholder': 'name@example.com',
            'required': True
        })
    )
    phone = forms.CharField(
        max_length=20,
        label="Mobile Phone Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_phone',
            'placeholder': '10-digit mobile number',
            'maxlength': '10',
            'inputmode': 'numeric',
            'pattern': '[6-9][0-9]{9}',
            'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);",
            'required': True
        })
    )
    alt_phone = forms.CharField(
        max_length=20,
        required=False,
        label="Alternative Phone Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_alt_phone',
            'placeholder': '10-digit alternative number',
            'maxlength': '10',
            'inputmode': 'numeric',
            'pattern': '[6-9][0-9]{9}',
            'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);"
        })
    )
    resume = forms.FileField(
        label="Upload Resume / Curriculum Vitae",
        validators=[validate_resume_file],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'id': 'id_resume',
            'accept': '.pdf,.docx,.doc',
            'required': True
        })
    )

    def __init__(self, *args, default_job=None, selected_job=None, fixed_job=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fixed_job = fixed_job or default_job or selected_job
        self.fields['job'].queryset = RecruitmentJob.objects.filter(
            status=RecruitmentJob.Status.OPEN
        ).select_related('department')
        if self.fixed_job:
            job_id = self.fixed_job.id if hasattr(self.fixed_job, 'id') else self.fixed_job
            self.fields['job'].initial = job_id
        elif self.fields['job'].queryset.count() == 1:
            self.fields['job'].initial = self.fields['job'].queryset.first().id

    def clean(self):
        cleaned_data = super().clean()
        job = cleaned_data.get('job')
        if not job and hasattr(self, 'fixed_job') and self.fixed_job:
            cleaned_data['job'] = self.fixed_job
            job = self.fixed_job
        if not job:
            self.add_error('job', "Please select the position you are applying for from the dropdown.")
        return cleaned_data





# -------------------------------------------------------------
# STAGE 2: POST-INTERVIEW ONBOARDING FORM (QUALIFIED CANDIDATES)
# -------------------------------------------------------------

class CandidateOnboardingForm(forms.Form):
    """
    Comprehensive Onboarding and Verification Form.
    Unlocked strictly AFTER the candidate successfully qualifies the interview rounds!
    Captures complete statutory IDs, full educational marksheets, bank details, and proofs.
    """
    # 1. Personal & Statutory Particulars
    date_of_birth = forms.DateField(
        label="Date of Birth",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True})
    )
    gender = forms.ChoiceField(
        choices=Candidate.GENDER_CHOICES,
        label="Gender",
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )
    father_name = forms.CharField(
        max_length=150,
        label="Father's / Guardian's Full Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Father's or Guardian's Name", 'required': True})
    )
    blood_group = forms.CharField(
        max_length=10,
        required=False,
        label="Blood Group",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. O+, A+, B+, AB+'})
    )
    marital_status = forms.ChoiceField(
        choices=[('SINGLE', 'Single'), ('MARRIED', 'Married'), ('OTHER', 'Other')],
        initial='SINGLE',
        label="Marital Status",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    emergency_contact_name = forms.CharField(
        max_length=150,
        label="Emergency Contact Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relative / Spouse / Parent', 'required': True})
    )
    emergency_contact_relation = forms.CharField(
        max_length=50,
        label="Relationship",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Father, Spouse, Sibling', 'required': True})
    )
    emergency_contact_phone = forms.CharField(
        max_length=20,
        label="Emergency Contact Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'id_emergency_contact_phone',
            'placeholder': '10-digit emergency number',
            'maxlength': '10',
            'inputmode': 'numeric',
            'pattern': '[6-9][0-9]{9}',
            'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);",
            'required': True
        })
    )
    current_address = forms.CharField(
        label="Current Residential Address",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'House/Flat No., Street, Area', 'required': True})
    )
    permanent_address = forms.CharField(
        label="Permanent Address",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Permanent Hometown Address', 'required': True})
    )
    state = forms.CharField(
        max_length=100,
        label="State / Province",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Karnataka', 'required': True})
    )
    postal_code = forms.CharField(
        max_length=20,
        label="Postal / PIN Code",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 560103', 'required': True})
    )
    photo = forms.ImageField(
        required=False,
        label="Passport Size Profile Photograph",
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
    )

    # 2. Comprehensive Educational History
    degree_name = forms.CharField(
        max_length=150,
        label="Exact Degree / Course Title",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Bachelor of Technology in Computer Science', 'required': True})
    )
    specialization = forms.CharField(
        max_length=150,
        required=False,
        label="Specialization / Branch",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science & Engineering'})
    )
    institution = forms.CharField(
        max_length=200,
        label="College / University Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Institution Name', 'required': True})
    )
    passing_year = forms.IntegerField(
        min_value=1970,
        max_value=2030,
        label="Graduation Year",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2023', 'required': True})
    )
    percentage_cgpa = forms.CharField(
        max_length=20,
        label="Aggregate Percentage / CGPA",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 8.6 CGPA or 82%', 'required': True})
    )
    details_10th = forms.CharField(
        max_length=150,
        label="10th Class (Board, School, Year & Score)",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. CBSE, Delhi Public School, 2017 - 94%', 'required': True})
    )
    details_12th = forms.CharField(
        max_length=150,
        label="12th / Intermediate / Diploma Details",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. State Board, 2019 - 89%', 'required': True})
    )
    educational_certificate = forms.FileField(
        required=False,
        label="Degree Certificate / Final Marksheet Upload",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'})
    )

    # 3. Employment & Experience Verification (Optional for freshers)
    previous_company = forms.CharField(
        max_length=150,
        required=False,
        label="Previous Employer Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prior Employer (if any)'})
    )
    previous_experience_details = forms.CharField(
        required=False,
        label="Prior Experience Summary",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Summary of prior responsibilities, designations, and tenures'})
    )
    experience_letter = forms.FileField(
        required=False,
        label="Relieving / Experience Letter Upload",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'})
    )
    payslip = forms.FileField(
        required=False,
        label="Recent Payslip / Form 16 Upload",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'})
    )

    # 4. Bank Account & Statutory Tax IDs
    bank_name = forms.CharField(
        max_length=150,
        label="Salary Bank Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. HDFC Bank, ICICI Bank, SBI', 'required': True})
    )
    bank_account_number = forms.CharField(
        max_length=50,
        label="Bank Account Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter 9 to 18-digit Account Number',
            'required': True,
            'maxlength': '18',
            'inputmode': 'numeric',
            'pattern': '[0-9]{9,18}',
            'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 18);"
        })
    )
    bank_ifsc_code = forms.CharField(
        max_length=20,
        label="Bank IFSC Code",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. HDFC0001234 (11 characters)',
            'required': True,
            'maxlength': '11',
            'pattern': '[A-Za-z]{4}0[A-Za-z0-9]{6}',
            'style': 'text-transform: uppercase;',
            'oninput': "this.value = this.value.toUpperCase().slice(0, 11);"
        })
    )
    bank_branch = forms.CharField(
        max_length=150,
        label="Bank Branch",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Koramangala Branch, Bengaluru', 'required': True})
    )
    pan_number = forms.CharField(
        max_length=20,
        label="Income Tax PAN Card Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. ABCDE1234F',
            'required': True,
            'maxlength': '10',
            'pattern': '[A-Za-z]{5}[0-9]{4}[A-Za-z]{1}',
            'style': 'text-transform: uppercase;',
            'oninput': "this.value = this.value.toUpperCase().slice(0, 10);"
        })
    )
    aadhaar_number = forms.CharField(
        max_length=20,
        label="Aadhaar / National ID Number",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '12-digit Aadhaar Number',
            'required': True,
            'maxlength': '12',
            'inputmode': 'numeric',
            'pattern': '[0-9]{12}',
            'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 12);"
        })
    )
    pf_uan_number = forms.CharField(
        max_length=20,
        required=False,
        label="PF UAN Number (Optional)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'UAN (Optional)',
            'maxlength': '12',
            'inputmode': 'numeric',
            'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 12);"
        })
    )
    bank_proof = forms.FileField(
        required=False,
        label="Cancelled Cheque / Bank Passbook Copy",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'})
    )
    id_proof = forms.FileField(
        required=False,
        label="Aadhaar / PAN Card Document Upload",
        validators=[validate_document_file],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.jpg,.jpeg,.png'})
    )

    # 5. Declaration
    accuracy_declaration = forms.BooleanField(
        required=True,
        label="I declare that all submitted personal, academic, and statutory details are authentic and accurate.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'required': True}),
        error_messages={'required': 'You must acknowledge the accuracy declaration to submit.'}
    )

    def clean_emergency_contact_phone(self):
        phone = self.cleaned_data.get('emergency_contact_phone', '').strip()
        digits = re.sub(r'\D', '', phone)
        if digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]
        elif digits.startswith('0') and len(digits) == 11:
            digits = digits[1:]
        if not re.match(r'^[6-9]\d{9}$', digits):
            raise ValidationError("Phone number must be exactly 10 digits starting with 6, 7, 8, or 9 (no letters or negative numbers).")
        return digits

    def clean_bank_account_number(self):
        acc = self.cleaned_data.get('bank_account_number', '').strip()
        digits = re.sub(r'\D', '', acc)
        if not re.match(r'^\d{9,18}$', digits):
            raise ValidationError("Bank account number must be between 9 and 18 digits (numbers only).")
        return digits

    def clean_bank_ifsc_code(self):
        ifsc = self.cleaned_data.get('bank_ifsc_code', '').strip().upper()
        if not re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', ifsc):
            raise ValidationError("IFSC Code must be exactly 11 characters (e.g. HDFC0001234): 4 uppercase letters, followed by 0, then 6 alphanumeric characters.")
        return ifsc

    def clean_pan_number(self):
        pan = self.cleaned_data.get('pan_number', '').strip().upper()
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan):
            raise ValidationError("Income Tax PAN must be exactly 10 characters in the format ABCDE1234F.")
        return pan

    def clean_aadhaar_number(self):
        aadhaar = self.cleaned_data.get('aadhaar_number', '').strip()
        digits = re.sub(r'\D', '', aadhaar)
        if not re.match(r'^\d{12}$', digits):
            raise ValidationError("Aadhaar number must be exactly 12 digits (numbers only).")
        return digits

    def clean_pf_uan_number(self):
        uan = self.cleaned_data.get('pf_uan_number', '').strip()
        if uan:
            digits = re.sub(r'\D', '', uan)
            if not re.match(r'^\d{12}$', digits):
                raise ValidationError("If provided, PF UAN number must be exactly 12 digits (numbers only).")
            return digits
        return ''


class AppointEmployeeForm(forms.Form):
    """
    Dedicated HR form for finalizing employee appointment,
    setting department/salary, and issuing HRMS portal login credentials.
    """
    application_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    candidate_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    lookup_query = forms.CharField(
        label="Candidate Phone No. or Registered Email",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'id': 'lookupQueryInput',
            'placeholder': 'Enter 10-digit mobile number or candidate email address...',
            'autocomplete': 'off'
        })
    )
    username = forms.CharField(
        label="Login User ID / Username",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control font-monospace fw-bold',
            'id': 'appointUsernameInput',
            'placeholder': 'e.g. chinmayee_mohanty_ux'
        })
    )
    password = forms.CharField(
        label="Create Password",
        max_length=128,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'appointPassInput',
            'placeholder': 'Create secure password (min 6 characters)',
            'minlength': '6'
        })
    )
    confirm_password = forms.CharField(
        label="Confirm Password",
        max_length=128,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'id': 'appointConfirmPassInput',
            'placeholder': 'Re-enter same password',
            'minlength': '6'
        })
    )

    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'appointDeptSelect'})
    )
    designation_title = forms.CharField(
        max_length=150,
        required=False,
        label="Designation / Position Title",
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'appointDesignationInput', 'placeholder': 'e.g. Senior Software Engineer'})
    )
    site = forms.ModelChoiceField(
        queryset=Site.objects.filter(is_active=True),
        required=False,
        label="Work Site / Location",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'appointSiteSelect'})
    )
    joining_date = forms.DateField(
        label="Official Joining Date",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'id': 'appointJoiningDateInput'}),
        required=True
    )
    employment_type = forms.ChoiceField(
        choices=[
            ('FULL_TIME', 'Full-time Permanent'),
            ('PROBATION', 'Probationary Period'),
            ('CONTRACT', 'Fixed Term Contract'),
            ('INTERN', 'Internship')
        ],
        initial='FULL_TIME',
        label="Employment Category",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    offered_ctc = forms.DecimalField(
        label="Annual CTC (INR)",
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'appointCtcInput', 'placeholder': 'e.g. 650000'})
    )
    basic_salary = forms.DecimalField(
        label="Monthly Basic Salary (INR)",
        max_digits=12,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'id': 'appointBasicSalaryInput', 'placeholder': 'e.g. 27000'})
    )
    confirm_appointment = forms.BooleanField(
        required=True,
        label="I confirm that all candidate documents are verified, compensation is approved, and this candidate is hereby appointed as an active company employee.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'appointCheckbox', 'required': True}),
        error_messages={'required': 'You must check the confirmation checkbox to appoint as an employee.'}
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password')
        p2 = cleaned_data.get('confirm_password')
        if p1 and p2:
            if len(p1) < 6:
                self.add_error('password', "Password must be at least 6 characters long.")
            if p1 != p2:
                self.add_error('confirm_password', "Passwords do not match. Please ensure both passwords match.")
        return cleaned_data


# -------------------------------------------------------------
# HR CANDIDATE REVIEW & SCHEDULING FORMS
# -------------------------------------------------------------

class ApplicationReviewForm(forms.ModelForm):
    """HR form to update candidate evaluation, status, and internal notes."""
    class Meta:
        model = JobApplication
        fields = ['status', 'rating', 'hr_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'rating': forms.Select(
                choices=[
                    (0, 'Unrated'),
                    (1, '1 - Poor'),
                    (2, '2 - Fair'),
                    (3, '3 - Average'),
                    (4, '4 - Strong'),
                    (5, '5 - Exceptional')
                ],
                attrs={'class': 'form-select'}
            ),
            'hr_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Confidential internal assessment, interview feedback, compensation notes...'
            }),
        }


class ScheduleInterviewForm(forms.ModelForm):
    """HR form to schedule an interview round for the candidate."""
    class Meta:
        model = JobApplication
        fields = [
            'interview_date', 'interview_time', 'interview_mode',
            'interview_location_link', 'interview_notes'
        ]
        widgets = {
            'interview_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'interview_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'interview_mode': forms.Select(attrs={'class': 'form-select'}),
            'interview_location_link': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. https://meet.google.com/abc-defg-hij or Boardroom 3, Bangalore HQ'
            }),
            'interview_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Interview round agenda, guidelines for candidate, technical prep notes...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
        self.fields['interview_date'].widget.attrs['min'] = today.strftime('%Y-%m-%d')

    def clean_interview_date(self):
        interview_date = self.cleaned_data.get('interview_date')
        if interview_date:
            today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
            if interview_date < today:
                raise forms.ValidationError("Invalid interview date. Date cannot be in the past (yesterday or earlier). Please choose today or a future date.")
        return interview_date

    def clean(self):
        cleaned_data = super().clean()
        interview_date = cleaned_data.get('interview_date')
        interview_time = cleaned_data.get('interview_time')
        today = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
        if interview_date and interview_date == today and interview_time:
            current_time = timezone.localtime().time() if hasattr(timezone, 'localtime') else timezone.now().time()
            if interview_time < current_time.replace(second=0, microsecond=0):
                self.add_error('interview_time', "Invalid interview time. For today's date, interview time cannot be in the past. Please select a future time slot.")
        return cleaned_data
