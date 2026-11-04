from django.db import models
from django.conf import settings
from employees.models import EmployeeProfile


class Goal(models.Model):
    STATUS_CHOICES = [
        ('NOT_STARTED', 'Not Started'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('ON_HOLD', 'On Hold'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    target_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_goals'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.employee.emp_id} ({self.progress_percentage}%)"


class PerformanceReview(models.Model):
    RATING_CHOICES = [
        (1, '1 - Unsatisfactory'),
        (2, '2 - Needs Improvement'),
        (3, '3 - Meets Expectations'),
        (4, '4 - Exceeds Expectations'),
        (5, '5 - Outstanding'),
    ]

    RECOMMENDATION_CHOICES = [
        ('NONE', 'Standard Progression'),
        ('PROMOTION', 'Recommended for Promotion'),
        ('SALARY_HIKE', 'Recommended for Salary Revision'),
        ('TRAINING', 'Needs Specialized Training'),
        ('PIP', 'Performance Improvement Plan'),
    ]

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted to HR'),
        ('APPROVED', 'Approved by Head / Management'),
    ]

    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='conducted_reviews'
    )
    review_cycle = models.CharField(max_length=50, help_text="e.g. Q1 2026, Mid-Year 2026, Annual 2026")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=3)
    strengths = models.TextField()
    areas_for_improvement = models.TextField()
    manager_remarks = models.TextField()
    employee_feedback = models.TextField(blank=True)
    recommendation = models.CharField(max_length=30, choices=RECOMMENDATION_CHOICES, default='NONE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Review {self.review_cycle} - {self.employee.emp_id} ({self.get_rating_display()})"


class EmployeeAward(models.Model):
    employee = models.ForeignKey(EmployeeProfile, on_delete=models.CASCADE, related_name='awards')
    award_title = models.CharField(max_length=150, help_text="e.g. Employee of the Month, Spot Award, Innovator of the Quarter")
    month_year = models.CharField(max_length=50, help_text="e.g. October 2026")
    citation = models.TextField(help_text="Detailed reason / accomplishment citation")
    awarded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='conferred_awards'
    )
    is_featured = models.BooleanField(default=True, help_text="Featured on Company Home Portal")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.award_title} - {self.employee.full_name} ({self.month_year})"
