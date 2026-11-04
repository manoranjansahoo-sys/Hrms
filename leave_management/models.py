from django.db import models
from django.conf import settings
from decimal import Decimal
from employees.models import EmployeeProfile


class LeaveType(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    days_per_year = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('12.0'))
    is_paid = models.BooleanField(default=True)
    requires_attachment = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class LeaveBalance(models.Model):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='leave_balances')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    year = models.PositiveIntegerField(default=2026)
    allocated_days = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('0.0'))
    used_days = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('0.0'))
    pending_days = models.DecimalField(max_digits=4, decimal_places=1, default=Decimal('0.0'))

    class Meta:
        unique_together = ('employee', 'leave_type', 'year')
        ordering = ['employee', 'leave_type']

    def __str__(self):
        return f"{self.employee.emp_id} - {self.leave_type.code}: {self.available_days} available"

    @property
    def available_days(self):
        # LOP has unlimited or 0 allocation
        if not self.leave_type.is_paid:
            return Decimal('999.0')
        return max(Decimal('0.0'), self.allocated_days - self.used_days - self.pending_days)


class LeaveRequest(models.Model):
    class Status(models.TextChoices):
        PENDING_MANAGER = 'PENDING_MANAGER', 'Pending Site Manager Approval'
        PENDING_HR = 'PENDING_HR', 'Pending HR Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled by Employee'

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='leave_requests')
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    is_half_day = models.BooleanField(default=False)
    half_day_period = models.CharField(
        max_length=20,
        choices=[('FIRST_HALF', 'First Half'), ('SECOND_HALF', 'Second Half')],
        blank=True
    )
    total_days = models.DecimalField(max_digits=4, decimal_places=1)
    reason = models.TextField()
    attachment = models.FileField(upload_to='leave_attachments/', blank=True, null=True)

    status = models.CharField(max_length=25, choices=Status.choices, default=Status.PENDING_MANAGER)

    manager_decision = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('RECOMMENDED', 'Recommended / Approved'), ('REJECTED', 'Rejected')],
        default='PENDING'
    )
    manager_remarks = models.TextField(blank=True)
    manager_action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='manager_reviewed_leaves'
    )
    manager_action_at = models.DateTimeField(null=True, blank=True)

    hr_decision = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
        default='PENDING'
    )
    hr_remarks = models.TextField(blank=True)
    hr_action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='hr_reviewed_leaves'
    )
    hr_action_at = models.DateTimeField(null=True, blank=True)

    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-applied_at']

    def __str__(self):
        return f"{self.employee.emp_id} - {self.leave_type.code} ({self.start_date} to {self.end_date}): {self.status}"
