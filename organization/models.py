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
