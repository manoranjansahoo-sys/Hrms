from django.db import models
from django.conf import settings


class Notification(models.Model):
    TYPE_CHOICES = [
        ('LEAVE', 'Leave Request'),
        ('ATTENDANCE', 'Attendance Update'),
        ('PAYROLL', 'Payroll & Payslip'),
        ('ANNOUNCEMENT', 'Company Announcement'),
        ('EVENT', 'Official Event'),
        ('BIRTHDAY', 'Birthday Reminder'),
        ('ANNIVERSARY', 'Work Anniversary'),
        ('PERFORMANCE', 'Performance Review'),
        ('SUPPORT', 'Support Ticket'),
        ('SYSTEM', 'System Alert'),
    ]

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='SYSTEM')
    target_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient.username}: {self.title} (Read: {self.is_read})"


def create_notification(recipient, title, message, notification_type='SYSTEM', target_url=''):
    """Helper to dispatch internal notifications safely."""
    try:
        return Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            target_url=target_url
        )
    except Exception:
        return None
