from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from accounts.models import CustomUser
from accounts.decorators import role_required, log_audit_trail
from performance.models import Goal, PerformanceReview, EmployeeAward
from employees.models import EmployeeProfile
from notifications.models import create_notification


@login_required
def goals_list(request):
    """View and track employee goals."""
    user = request.user
    emp_profile = getattr(user, 'employee_profile', None)

    if user.is_site_manager_role or user.is_hr_role or user.is_head_role:
        # Managers can see their team goals or create new ones
        if user.is_site_manager_role and not (user.is_hr_role or user.is_head_role):
            goals = Goal.objects.filter(employee__site__in=user.managed_sites.all()).select_related('employee__user')
            employees = EmployeeProfile.objects.filter(site__in=user.managed_sites.all(), status='ACTIVE')
        else:
            goals = Goal.objects.all().select_related('employee__user')
            employees = EmployeeProfile.objects.filter(status='ACTIVE')
    else:
        goals = Goal.objects.filter(employee=emp_profile).select_related('employee__user')
        employees = []

    return render(request, 'performance/goals_list.html', {
        'goals': goals,
        'employees': employees,
        'emp_profile': emp_profile,
    })


@login_required
def assign_goal(request):
    """Site Manager or HR assigns a performance goal to an employee."""
    if request.method == 'POST':
        emp_id = request.POST.get('employee_id')
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        target_date = request.POST.get('target_date')

        emp = get_object_or_404(EmployeeProfile, id=emp_id)
        goal = Goal.objects.create(
            employee=emp,
            title=title,
            description=description,
            target_date=target_date,
            assigned_by=request.user,
            status='IN_PROGRESS',
            progress_percentage=0
        )

        create_notification(
            recipient=emp.user,
            title='New Performance Goal Assigned',
            message=f"Goal '{title}' has been assigned to you by {request.user.get_full_name()}.",
            notification_type='PERFORMANCE',
            target_url='/performance/goals/'
        )
        messages.success(request, f"Goal assigned to {emp.full_name} successfully.")
    return redirect('performance:goals_list')


@login_required
def update_goal_progress(request, goal_id):
    """Update goal status and percentage."""
    goal = get_object_or_404(Goal, id=goal_id)
    if request.method == 'POST':
        pct = int(request.POST.get('progress_percentage', goal.progress_percentage))
        status = request.POST.get('status', goal.status)
        goal.progress_percentage = min(100, max(0, pct))
        goal.status = status
        if goal.progress_percentage == 100:
            goal.status = 'COMPLETED'
        goal.save()
        messages.success(request, f"Goal '{goal.title}' updated ({goal.progress_percentage}%).")
    return redirect('performance:goals_list')


@login_required
def reviews_list(request):
    """View performance reviews and awards."""
    user = request.user
    emp_profile = getattr(user, 'employee_profile', None)

    if user.is_hr_role or user.is_head_role or user.is_site_manager_role:
        reviews = PerformanceReview.objects.select_related('employee__user', 'reviewer').all()
        employees = EmployeeProfile.objects.filter(status='ACTIVE')
    else:
        reviews = PerformanceReview.objects.filter(employee=emp_profile, status='APPROVED').select_related('employee__user', 'reviewer')
        employees = []

    awards = EmployeeAward.objects.select_related('employee__user').all()

    return render(request, 'performance/reviews_list.html', {
        'reviews': reviews,
        'employees': employees,
        'awards': awards,
    })


@login_required
@role_required([CustomUser.Role.SITE_MANAGER, CustomUser.Role.HR, CustomUser.Role.HEAD])
def create_review(request):
    """Managers or HR create a performance evaluation."""
    if request.method == 'POST':
        emp_id = request.POST.get('employee_id')
        review_cycle = request.POST.get('review_cycle')
        rating = int(request.POST.get('rating', 3))
        strengths = request.POST.get('strengths', '')
        areas = request.POST.get('areas_for_improvement', '')
        remarks = request.POST.get('manager_remarks', '')
        recommendation = request.POST.get('recommendation', 'NONE')

        emp = get_object_or_404(EmployeeProfile, id=emp_id)

        review = PerformanceReview.objects.create(
            employee=emp,
            reviewer=request.user,
            review_cycle=review_cycle,
            rating=rating,
            strengths=strengths,
            areas_for_improvement=areas,
            manager_remarks=remarks,
            recommendation=recommendation,
            status='APPROVED' if (request.user.is_head_role or request.user.is_hr_role) else 'SUBMITTED'
        )

        create_notification(
            recipient=emp.user,
            title='Performance Review Recorded',
            message=f"Performance evaluation for {review_cycle} has been recorded by {request.user.get_full_name()}.",
            notification_type='PERFORMANCE',
            target_url='/performance/reviews/'
        )

        messages.success(request, f"Performance review for {emp.full_name} submitted successfully.")
    return redirect('performance:reviews_list')
