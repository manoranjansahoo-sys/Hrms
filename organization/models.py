from django.db import models
from django.conf import settings


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    head_of_department = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='headed_departments'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def employee_count(self):
        return self.employees.filter(status='ACTIVE').count()


class Designation(models.Model):
    title = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='designations')
    grade_level = models.CharField(max_length=20, blank=True, help_text="e.g. L1, L2, L3, Lead, Principal")
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['department', 'title']
        unique_together = ('title', 'department')

    def __str__(self):
        return f"{self.title} - {self.department.name}"


class Site(models.Model):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=20, unique=True)
    city = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    site_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_sites'
    )
    contact_phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Company Location'
        verbose_name_plural = 'Company Locations (Admin Setup)'

    def __str__(self):
        return f"{self.name} - {self.city} ({self.code})"

    @property
    def employee_count(self):
        return self.employees.filter(status='ACTIVE').count()


class Holiday(models.Model):
    class HolidayType(models.TextChoices):
        PUBLIC = 'PUBLIC', 'Public Holiday'
        FESTIVAL = 'FESTIVAL', 'Festival Holiday'
        RESTRICTED = 'RESTRICTED', 'Restricted Holiday'
        COMPANY = 'COMPANY', 'Company Declared Holiday'

    title = models.CharField(max_length=150)
    holiday_type = models.CharField(max_length=20, choices=HolidayType.choices, default=HolidayType.PUBLIC)
    date = models.DateField(unique=True)
    description = models.TextField(blank=True)
    is_optional = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f"{self.title} ({self.date.strftime('%d %b %Y')})"


class CompanyEvent(models.Model):
    EVENT_TYPES = [
        ('CELEBRATION', 'Celebration / Festival'),
        ('MEETING', 'Town Hall / Company Meeting'),
        ('TRAINING', 'Training / Workshop'),
        ('OUTING', 'Team Outing / Social Activity'),
        ('OTHER', 'General Event'),
    ]

    title = models.CharField(max_length=200)
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES, default='CELEBRATION')
    venue = models.CharField(max_length=200)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    description = models.TextField()
    cover_image = models.ImageField(upload_to='events/covers/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_datetime']

    def __str__(self):
        return f"{self.title} ({self.start_datetime.strftime('%d %b %Y')})"


class EventParticipant(models.Model):
    event = models.ForeignKey(CompanyEvent, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_registrations')
    registered_at = models.DateTimeField(auto_now_add=True)
    attended = models.BooleanField(default=False)

    class Meta:
        unique_together = ('event', 'user')

    def __str__(self):
        return f"{self.user} - {self.event.title}"


class EventGallery(models.Model):
    event = models.ForeignKey(CompanyEvent, on_delete=models.CASCADE, related_name='photos', null=True, blank=True)
    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to='events/gallery/')
    caption = models.CharField(max_length=255, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.title


class Announcement(models.Model):
    CATEGORY_CHOICES = [
        ('HR', 'HR Notice'),
        ('MANAGEMENT', 'Management Directive'),
        ('EMERGENCY', 'Emergency Alert'),
        ('POLICY', 'Policy Update'),
        ('GENERAL', 'Company News'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('HIGH', 'High Priority'),
        ('URGENT', 'Urgent Alert'),
    ]

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='GENERAL')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='MEDIUM')
    content = models.TextField()
    attachment = models.FileField(upload_to='announcements/', blank=True, null=True)
    target_site = models.ForeignKey(Site, null=True, blank=True, on_delete=models.SET_NULL)
    target_department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    is_pinned = models.BooleanField(default=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_pinned', '-created_at']

    def __str__(self):
        return f"[{self.priority}] {self.title}"


class AnnouncementRead(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='reads')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='read_announcements')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('announcement', 'user')


class CompanyPolicy(models.Model):
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=100, default='General Policy')
    document = models.FileField(upload_to='policies/', blank=True, null=True)
    summary = models.TextField()
    effective_date = models.DateField()
    requires_acknowledgement = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-effective_date']

    def __str__(self):
        return self.title


class PolicyAcknowledgement(models.Model):
    policy = models.ForeignKey(CompanyPolicy, on_delete=models.CASCADE, related_name='acknowledgements')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='policy_acknowledgements')
    acknowledged_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('policy', 'user')


class OperatingSchedule(models.Model):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    day_of_week = models.IntegerField(choices=DAY_CHOICES, unique=True)
    day_name = models.CharField(max_length=20)
    is_working_day = models.BooleanField(
        default=True,
        help_text="Designates whether this day is a working day or weekly off."
    )
    opening_time = models.TimeField(default='09:30:00')
    closing_time = models.TimeField(default='18:30:00')
    grace_period_minutes = models.PositiveIntegerField(default=15)
    notes = models.CharField(max_length=255, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_of_week']
        verbose_name = 'Operating Schedule'
        verbose_name_plural = 'Operating Schedules'

    def __str__(self):
        status = "Working Day" if self.is_working_day else "Weekly Off"
        op_str = self.opening_time.strftime('%I:%M %p') if hasattr(self.opening_time, 'strftime') else str(self.opening_time)
        cl_str = self.closing_time.strftime('%I:%M %p') if hasattr(self.closing_time, 'strftime') else str(self.closing_time)
        return f"{self.day_name}: {status} ({op_str} - {cl_str})"

    @classmethod
    def get_weekly_schedule(cls):
        """Returns 7 days schedule, automatically seeding defaults if not present."""
        if cls.objects.count() < 7:
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            for d_idx, d_name in enumerate(day_names):
                is_work = (d_idx != 6)  # Sunday is weekly off
                cls.objects.get_or_create(
                    day_of_week=d_idx,
                    defaults={
                        'day_name': d_name,
                        'is_working_day': is_work,
                        'opening_time': '09:30:00',
                        'closing_time': '18:30:00',
                        'grace_period_minutes': 15,
                        'notes': 'Company standard business hours' if is_work else 'Sunday Company Weekly Off'
                    }
                )
        return cls.objects.all().order_by('day_of_week')


class MasterDataPermission(models.Model):
    """
    Controls access to the unified Master Data Control Center.
    By default only Admin (Head / Superuser) has access.
    Admin can toggle access to all HR or assign specific users/positions.
    """
    singleton_id = models.IntegerField(default=1, unique=True)
    allow_all_hr = models.BooleanField(
        default=False,
        help_text="When enabled, any user with HR Administrator role can view and update Master Data."
    )
    allowed_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='master_data_delegations',
        help_text="Specific users/employees delegated access to Master Data."
    )
    can_manage_holidays = models.BooleanField(default=True, help_text="Delegated users can manage holiday calendar.")
    can_manage_timings = models.BooleanField(default=True, help_text="Delegated users can manage opening/closing hours.")
    can_manage_locations = models.BooleanField(default=True, help_text="Delegated users can add/update/delete company sites.")
    can_manage_leave_policy = models.BooleanField(default=True, help_text="Delegated users can update Sick & Paid leave quotas.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Master Data Permission'
        verbose_name_plural = 'Master Data Permissions'

    def __str__(self):
        return f"Master Data Permissions (HR Access: {'Enabled' if self.allow_all_hr else 'Disabled'})"

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(singleton_id=1)
        return obj

    @classmethod
    def can_user_access(cls, user, section=None):
        if not user or not user.is_authenticated:
            return False
        # Head / Super Admin always has full access
        if user.is_superuser or getattr(user, 'role', None) == 'head':
            return True

        settings_obj = cls.get_settings()

        has_role_access = (getattr(user, 'role', None) == 'hr' and settings_obj.allow_all_hr)
        has_user_access = settings_obj.allowed_users.filter(id=user.id).exists()

        if not (has_role_access or has_user_access):
            return False

        if section == 'holidays' and not settings_obj.can_manage_holidays:
            return False
        if section == 'timings' and not settings_obj.can_manage_timings:
            return False
        if section == 'locations' and not settings_obj.can_manage_locations:
            return False
        if section == 'leave_policy' and not settings_obj.can_manage_leave_policy:
            return False

        return True

