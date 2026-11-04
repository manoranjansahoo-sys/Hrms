from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    class Role(models.TextChoices):
        EMPLOYEE = 'employee', 'Employee'
        HR = 'hr', 'HR Administrator'
        SITE_MANAGER = 'site_manager', 'Site Manager'
        HEAD = 'head', 'Head / Super Admin'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.EMPLOYEE,
        help_text="Designated authority level within the HRMS."
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_verified = models.BooleanField(default=True)
    theme_preference = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='light'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['username']

    def __str__(self):
        full_name = self.get_full_name()
        return f"{full_name or self.username} ({self.get_role_display()})"

    @property
    def is_employee_role(self):
        return self.role == self.Role.EMPLOYEE

    @property
    def is_hr_role(self):
        return self.role == self.Role.HR or self.is_superuser

    @property
    def is_site_manager_role(self):
        return self.role == self.Role.SITE_MANAGER

    @property
    def is_head_role(self):
        return self.role == self.Role.HEAD or self.is_superuser

    @property
    def can_access_hr_modules(self):
        return self.role in [self.Role.HR, self.Role.HEAD] or self.is_superuser

    @property
    def can_access_site_manager_modules(self):
        return self.role in [self.Role.SITE_MANAGER, self.Role.HR, self.Role.HEAD] or self.is_superuser

    @property
    def can_access_head_modules(self):
        return self.role == self.Role.HEAD or self.is_superuser

    def get_avatar_url(self):
        if self.avatar and hasattr(self.avatar, 'url'):
            return self.avatar.url
        return f"https://ui-avatars.com/api/?name={self.first_name}+{self.last_name}&background=1B5E20&color=fff&size=128"


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('CREATE', 'Record Created'),
        ('UPDATE', 'Record Updated'),
        ('DELETE', 'Record Deleted'),
        ('APPROVAL', 'Approval Action'),
        ('PAYROLL', 'Payroll Processed'),
        ('ATTENDANCE_CORRECTION', 'Attendance Correction'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    module = models.CharField(max_length=50)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.created_at.strftime('%Y-%m-%d %H:%M')}] {self.user} - {self.action}: {self.module}"
