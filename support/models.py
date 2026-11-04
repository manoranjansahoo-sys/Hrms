from django.db import models
from django.conf import settings
from employees.models import EmployeeProfile


class OfficialDocumentRequest(models.Model):
    DOC_CHOICES = [
        ('EXPERIENCE_LETTER', 'Experience / Relieving Letter'),
        ('EMPLOYMENT_CERTIFICATE', 'Certificate of Employment / Address Proof'),
        ('ID_CARD', 'Digital / Physical ID Card Reissue'),
        ('SALARY_CERTIFICATE', 'Salary Certificate (Visa/Loan)'),
        ('BONAFIDE', 'Bonafide Letter'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending HR Review'),
        ('PROCESSING', 'In Preparation'),
        ('ISSUED', 'Issued / Completed'),
        ('REJECTED', 'Rejected'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='document_requests')
    document_type = models.CharField(max_length=30, choices=DOC_CHOICES)
    purpose = models.TextField(help_text="Reason or required destination for this document")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    issued_document = models.FileField(upload_to='issued_documents/', null=True, blank=True)
    hr_remarks = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processed_document_requests'
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-requested_at']

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.employee.emp_id} ({self.status})"


class SupportTicket(models.Model):
    CATEGORY_CHOICES = [
        ('IT_SUPPORT', 'IT & Hardware / Software Issue'),
        ('WORKPLACE', 'Workplace & Facility Request'),
        ('HR_QUERY', 'HR Policy & Benefits Query'),
        ('GRIEVANCE', 'Confidential Grievance / Workplace Issue'),
    ]

    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('IN_PROGRESS', 'In Progress'),
        ('RESOLVED', 'Resolved'),
        ('CLOSED', 'Closed'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='support_tickets')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='IT_SUPPORT')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    subject = models.CharField(max_length=200)
    description = models.TextField()
    attachment = models.FileField(upload_to='ticket_attachments/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OPEN')

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets'
    )
    resolution_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.category}] {self.subject} ({self.get_status_display()})"


class TicketComment(models.Model):
    ticket = models.ForeignKey(SupportTicket, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user} on #{self.ticket.id}"


class Asset(models.Model):
    TYPE_CHOICES = [
        ('LAPTOP', 'Laptop / Computer'),
        ('MONITOR', 'External Monitor'),
        ('PHONE', 'Smartphone / SIM Card'),
        ('PERIPHERAL', 'Peripheral / Keyboard / Mouse'),
        ('FURNITURE', 'Ergonomic Chair / Desk'),
        ('OTHER', 'Other Corporate Asset'),
    ]

    STATUS_CHOICES = [
        ('AVAILABLE', 'Available in Stock'),
        ('ASSIGNED', 'Assigned to Employee'),
        ('MAINTENANCE', 'In Repair / Maintenance'),
        ('RETIRED', 'Retired / Scrapped'),
    ]

    asset_tag = models.CharField(max_length=50, unique=True, help_text="Unique asset barcode / tag")
    name = models.CharField(max_length=150)
    asset_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='LAPTOP')
    serial_number = models.CharField(max_length=100, blank=True)
    assigned_to = models.ForeignKey(
        EmployeeProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_assets'
    )
    assigned_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    specifications = models.TextField(blank=True, help_text="RAM, SSD, processor, model details")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['asset_tag']

    def __str__(self):
        return f"{self.asset_tag} - {self.name} ({self.get_status_display()})"
