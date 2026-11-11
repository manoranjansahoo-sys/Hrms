import re
from django import forms
from employees.models import EmployeeProfile, EmployeeDocument, ProfileCorrectionRequest
from organization.models import Department, Designation, Site
from accounts.models import CustomUser


class EmployeeCreateForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name', 'required': True})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name', 'required': True})
    )
    username = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username / User ID', 'required': True})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Work Email', 'required': True})
    )
    phone = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Primary mobile number',
            'required': True,
            'maxlength': '10',
            'inputmode': 'numeric',
            'pattern': '[6-9][0-9]{9}',
            'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);",
            'id': 'id_phone'
        })
    )
    password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create password',
            'required': True,
            'minlength': '6',
            'id': 'id_password'
        })
    )
    confirm_password = forms.CharField(
        max_length=128,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Re-enter password',
            'required': True,
            'minlength': '6',
            'id': 'id_confirm_password'
        })
    )
    role = forms.ChoiceField(
        choices=CustomUser.Role.choices,
        initial=CustomUser.Role.EMPLOYEE,
        widget=forms.Select(attrs={'class': 'form-select', 'required': True})
    )

    class Meta:
        model = EmployeeProfile
        fields = [
            'department', 'designation', 'site', 'reporting_manager',
            'employment_type', 'joining_date', 'date_of_birth',
            'gender', 'marital_status', 'blood_group',
            'city', 'address', 'postal_code',
            'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relation',
            'bank_name', 'bank_account_number', 'ifsc_code', 'pan_number', 'uan_number',
            'education_details', 'experience_summary'
        ]
        widgets = {
            'department': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'designation': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'site': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'reporting_manager': forms.Select(attrs={'class': 'form-select'}),
            'employment_type': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
            'gender': forms.Select(attrs={'class': 'form-select', 'required': True}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Blood Group (e.g. O+)'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Residential address'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'PIN Code'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Emergency contact person'}),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Emergency phone number',
                'maxlength': '10',
                'inputmode': 'numeric',
                'pattern': '[6-9][0-9]{9}',
                'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);",
                'required': True
            }),
            'emergency_contact_relation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Relation (e.g. Father, Spouse)'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Salary bank name', 'required': True}),
            'bank_account_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Bank account number',
                'maxlength': '18',
                'inputmode': 'numeric',
                'pattern': '[0-9]{9,18}',
                'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 18);",
                'required': True
            }),
            'ifsc_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. HDFC0001234',
                'maxlength': '11',
                'pattern': '[A-Za-z]{4}0[A-Za-z0-9]{6}',
                'style': 'text-transform: uppercase;',
                'oninput': "this.value = this.value.toUpperCase().slice(0, 11);",
                'required': True
            }),
            'pan_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. ABCDE1234F',
                'maxlength': '10',
                'pattern': '[A-Za-z]{5}[0-9]{4}[A-Za-z]{1}',
                'style': 'text-transform: uppercase;',
                'oninput': "this.value = this.value.toUpperCase().slice(0, 10);",
                'required': True
            }),
            'uan_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'UAN (Optional)',
                'maxlength': '12',
                'inputmode': 'numeric',
                'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 12);"
            }),
            'education_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': ''}),
            'experience_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': ''}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Role authority restriction: Admin/Head/Superuser can assign all roles.
        # HR administrator can strictly assign only Employee and Site Manager.
        if user and not (user.is_superuser or getattr(user, 'role', '') == CustomUser.Role.HEAD):
            self.fields['role'].choices = [
                (CustomUser.Role.EMPLOYEE, 'Employee'),
                (CustomUser.Role.SITE_MANAGER, 'Site Manager'),
            ]

        required_fields = [
            'department', 'designation', 'site', 'employment_type',
            'joining_date', 'date_of_birth', 'gender',
            'emergency_contact_phone', 'bank_name', 'bank_account_number',
            'ifsc_code', 'pan_number'
        ]
        for field in required_fields:
            if field in self.fields:
                self.fields[field].required = True
        if 'uan_number' in self.fields:
            self.fields['uan_number'].required = False
        if 'marital_status' in self.fields:
            self.fields['marital_status'].required = False
            self.fields['marital_status'].initial = 'SINGLE'

    def clean_role(self):
        role = self.cleaned_data.get('role')
        if self.user and not (self.user.is_superuser or getattr(self.user, 'role', '') == CustomUser.Role.HEAD):
            allowed_roles = [CustomUser.Role.EMPLOYEE, CustomUser.Role.SITE_MANAGER]
            if role not in allowed_roles:
                raise forms.ValidationError("HR administrators are authorized to onboard Employee and Site Manager roles only.")
        return role

    def clean_marital_status(self):
        status = self.cleaned_data.get('marital_status')
        return status or 'SINGLE'

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        digits = re.sub(r'\D', '', phone)
        if digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]
        elif digits.startswith('0') and len(digits) == 11:
            digits = digits[1:]
        if not re.match(r'^[6-9]\d{9}$', digits):
            raise forms.ValidationError("Mobile phone number must be exactly 10 digits starting with 6, 7, 8, or 9.")
        return digits

    def clean_emergency_contact_phone(self):
        phone = self.cleaned_data.get('emergency_contact_phone', '').strip()
        digits = re.sub(r'\D', '', phone)
        if digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]
        elif digits.startswith('0') and len(digits) == 11:
            digits = digits[1:]
        if not re.match(r'^[6-9]\d{9}$', digits):
            raise forms.ValidationError("Emergency phone number must be exactly 10 digits starting with 6, 7, 8, or 9 (no letters or negative numbers).")
        return digits

    def clean_bank_account_number(self):
        acc = self.cleaned_data.get('bank_account_number', '').strip()
        digits = re.sub(r'\D', '', acc)
        if not re.match(r'^\d{9,18}$', digits):
            raise forms.ValidationError("Bank account number must be between 9 and 18 digits (numbers only).")
        return digits

    def clean_ifsc_code(self):
        ifsc = self.cleaned_data.get('ifsc_code', '').strip().upper()
        if not re.match(r'^[A-Z]{4}0[A-Z0-9]{6}$', ifsc):
            raise forms.ValidationError("IFSC Code must be exactly 11 characters (e.g. HDFC0001234): 4 uppercase letters, followed by 0, then 6 alphanumeric characters.")
        return ifsc

    def clean_pan_number(self):
        pan = self.cleaned_data.get('pan_number', '').strip().upper()
        if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$', pan):
            raise forms.ValidationError("Income Tax PAN must be exactly 10 characters in the format ABCDE1234F.")
        return pan

    def clean_uan_number(self):
        uan = self.cleaned_data.get('uan_number', '').strip()
        if uan:
            digits = re.sub(r'\D', '', uan)
            if not re.match(r'^\d{12}$', digits):
                raise forms.ValidationError("If provided, PF UAN number must be exactly 12 digits (numbers only).")
            return digits
        return ''

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


CORRECTION_FIELD_CHOICES = [
    ('', '-- Select Field to Update --'),
    ('Mobile Phone Number', 'Mobile Phone Number'),
    ('Personal Email', 'Personal / Alternate Email'),
    ('Salary Bank Name', 'Salary Bank Name'),
    ('Bank Account Number', 'Bank Account Number'),
    ('Bank IFSC Code', 'Bank IFSC Code'),
    ('PAN Card Number', 'PAN Card Number'),
    ('PF UAN Number', 'PF UAN Number'),
    ('Emergency Contact Phone', 'Emergency Contact Phone'),
    ('Emergency Contact Name', 'Emergency Contact Person'),
    ('Emergency Contact Relation', 'Emergency Contact Relation'),
    ('Residential Address', 'Residential Address'),
    ('City', 'City'),
    ('State', 'State'),
    ('Postal / PIN Code', 'Postal / PIN Code'),
    ('Blood Group', 'Blood Group'),
    ('Marital Status', 'Marital Status'),
    ('Educational Details', 'Educational Qualifications'),
    ('Prior Experience Overview', 'Prior Experience Overview'),
    ('Other', 'Other Field (Specify)'),
]


class ProfileCorrectionForm(forms.ModelForm):
    field_select = forms.ChoiceField(
        choices=CORRECTION_FIELD_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_field_select'})
    )
    custom_field = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'id_custom_field', 'placeholder': 'Specify custom field name'})
    )

    class Meta:
        model = ProfileCorrectionRequest
        fields = ['field_name', 'current_value', 'proposed_value', 'reason']
        widgets = {
            'field_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Field name',
                'id': 'id_field_name',
                'required': True
            }),
            'current_value': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Existing value on record',
                'id': 'id_current_value'
            }),
            'proposed_value': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Proposed new value',
                'id': 'id_proposed_value',
                'required': True
            }),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Reason for correction / supporting context',
                'required': True
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        f_name = cleaned_data.get('field_name')
        f_select = cleaned_data.get('field_select')
        c_field = cleaned_data.get('custom_field')

        if f_select == 'Other' and c_field:
            cleaned_data['field_name'] = c_field
        elif f_select and not f_name:
            cleaned_data['field_name'] = f_select
        return cleaned_data
