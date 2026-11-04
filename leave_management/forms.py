from django import forms
from leave_management.models import LeaveRequest, LeaveType


class LeaveApplicationForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'is_half_day', 'half_day_period', 'reason', 'attachment']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_half_day': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'halfDayCheck'}),
            'half_day_period': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Provide specific reason for absence'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }

