from django import forms
from leave_management.models import LeaveRequest, LeaveType


class LeaveApplicationForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['leave_type'].queryset = LeaveType.objects.filter(code__in=['SL', 'PL']).order_by('name')
        self.fields['end_date'].required = False
        self.fields['half_day_period'].required = False

    def clean(self):
        cleaned_data = super().clean()
        is_half_day = cleaned_data.get('is_half_day')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if is_half_day:
            if start_date:
                cleaned_data['end_date'] = start_date
        else:
            if not end_date:
                self.add_error('end_date', 'End date is required for full-day leave.')
            elif start_date and end_date < start_date:
                self.add_error('end_date', 'End date cannot be earlier than start date.')

        return cleaned_data

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

