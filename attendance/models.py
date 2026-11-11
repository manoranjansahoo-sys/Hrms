from django.db import models
from django.conf import settings
from decimal import Decimal
from employees.models import EmployeeProfile


class Shift(models.Model):
    name = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    grace_period_minutes = models.PositiveIntegerField(default=15)
    half_day_hours = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('4.5'))
    full_day_hours = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('8.0'))
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('PRESENT', 'Present'),
        ('ABSENT', 'Absent'),
        ('HALF_DAY', 'Half Day'),
        ('ON_LEAVE', 'On Leave'),
        ('HOLIDAY', 'Holiday'),
        ('WEEK_OFF', 'Weekly Off'),
    ]

    SOURCE_CHOICES = [
        ('WEB', 'Web Self-Service'),
        ('KIOSK', 'Office Kiosk'),
        ('BIOMETRIC', 'Biometric / Access Device'),
        ('MANUAL', 'HR Manual Override'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(db_index=True)
    shift = models.ForeignKey(Shift, on_delete=models.SET_NULL, null=True, blank=True)
    punch_in = models.DateTimeField(null=True, blank=True)
    punch_out = models.DateTimeField(null=True, blank=True)
    working_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    break_duration_minutes = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ABSENT')
    is_late = models.BooleanField(default=False)
    is_early_departure = models.BooleanField(default=False)
    overtime_hours = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    punch_in_ip = models.GenericIPAddressField(null=True, blank=True)
    punch_out_ip = models.GenericIPAddressField(null=True, blank=True)
    device_source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='WEB')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', 'employee']
        unique_together = ('employee', 'date')

    def __str__(self):
        return f"{self.employee.emp_id} - {self.date} ({self.get_status_display()})"

    def calculate_hours(self):
        """Calculates working hours and overtime if both punch_in and punch_out exist."""
        if self.punch_in and self.punch_out:
            duration = (self.punch_out - self.punch_in).total_seconds()
            hours = Decimal(str(round(max(0, duration / 3600), 2)))
            self.working_hours = hours

            shift_hours = self.shift.full_day_hours if self.shift else Decimal('8.00')
            half_day_hours = self.shift.half_day_hours if self.shift else Decimal('4.50')

            if hours >= shift_hours:
                self.status = 'PRESENT'
                self.overtime_hours = max(Decimal('0.00'), hours - shift_hours)
            elif hours >= half_day_hours:
                self.status = 'HALF_DAY'
                self.overtime_hours = Decimal('0.00')
            else:
                self.status = 'ABSENT'
                self.overtime_hours = Decimal('0.00')

    @property
    def late_duration_text(self):
        """Returns human-readable late duration string, e.g. 'Late by 25 min' or 'Late by 1h 15m'."""
        if not self.is_late or not self.punch_in:
            return ""
        from django.utils import timezone
        from datetime import time
        shift = self.shift
        if not shift:
            shift = Shift.objects.filter(is_default=True).first() or Shift.objects.first()
        start_t = shift.start_time if (shift and shift.start_time) else time(9, 30)
        pin_local = timezone.localtime(self.punch_in)
        shift_start_dt = pin_local.replace(hour=start_t.hour, minute=start_t.minute, second=0, microsecond=0)
        if pin_local > shift_start_dt:
            diff_sec = int((pin_local - shift_start_dt).total_seconds())
            diff_min = max(1, diff_sec // 60)
            hours = diff_min // 60
            mins = diff_min % 60
            if hours > 0 and mins > 0:
                return f"Late by {hours}h {mins}m"
            elif hours > 0:
                return f"Late by {hours} hr"
            else:
                return f"Late by {mins} min"
        return "Late"

    @property
    def arrival_display(self):
        """Returns 'On Time', 'Late by ...', or '' if absent/unrecorded."""
        if not self.punch_in or self.status in ['ABSENT', 'ON_LEAVE', 'WEEK_OFF', 'HOLIDAY']:
            return ""
        if self.is_late:
            return self.late_duration_text or "Late"
        return "On Time"


class AttendanceCorrectionRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    attendance = models.ForeignKey(Attendance, on_delete=models.SET_NULL, null=True, blank=True, related_name='correction_requests')
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='attendance_corrections')
    date = models.DateField()
    requested_punch_in = models.DateTimeField(null=True, blank=True)
    requested_punch_out = models.DateTimeField(null=True, blank=True)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_attendance_corrections'
    )
    review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Correction for {self.employee.emp_id} on {self.date} ({self.status})"


class AttendanceAuditLog(models.Model):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=100)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    previous_data = models.TextField(blank=True)
    new_data = models.TextField(blank=True)
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Audit: {self.attendance} - {self.action} at {self.timestamp}"
