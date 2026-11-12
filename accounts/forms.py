import re
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.db.models import Q
from accounts.models import CustomUser


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'autocomplete': 'username',
            'autocapitalize': 'none',
            'spellcheck': 'false',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'current-password',
        })
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username and password:
            lookup_username = username.strip()
            if '@' in lookup_username:
                user_match = CustomUser.objects.filter(email__iexact=lookup_username).first()
                if user_match:
                    lookup_username = user_match.username
            else:
                digits = re.sub(r'\D', '', lookup_username)
                if len(digits) >= 10:
                    ten_digit = digits[-10:]
                    user_match = CustomUser.objects.filter(
                        Q(phone=lookup_username) |
                        Q(phone=ten_digit) |
                        Q(phone__endswith=ten_digit) |
                        Q(employee_profile__emergency_contact_phone__endswith=ten_digit)
                    ).first()
                    if user_match:
                        lookup_username = user_match.username

            self.user_cache = authenticate(self.request, username=lookup_username, password=password)
            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)
        return self.cleaned_data


import re

class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'theme_preference', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'id_phone',
                'placeholder': '10-digit mobile number',
                'maxlength': '10',
                'inputmode': 'numeric',
                'pattern': '[6-9][0-9]{9}',
                'oninput': "this.value = this.value.replace(/[^0-9]/g, '').slice(0, 10);"
            }),
            'theme_preference': forms.Select(attrs={'class': 'form-select'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        if not phone:
            return ''
        digits = re.sub(r'\D', '', phone)
        if digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]
        elif digits.startswith('0') and len(digits) == 11:
            digits = digits[1:]
        if not re.match(r'^[6-9]\d{9}$', digits):
            raise forms.ValidationError("Mobile phone number must be exactly 10 digits starting with 6, 7, 8, or 9.")
        return digits
