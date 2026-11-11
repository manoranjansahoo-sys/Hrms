from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, date
from django.db.models import Count, Sum, Q, Avg
from decimal import Decimal
from accounts.models import CustomUser, AuditLog
from accounts.decorators import role_required, hr_required, site_manager_required, head_required
from organization.models import Department, Site, Holiday, CompanyEvent, Announcement, CompanyPolicy, EventParticipant
from employees.models import EmployeeProfile, ProfileCorrectionRequest
from attendance.models import Attendance, AttendanceCorrectionRequest
from leave_management.models import LeaveRequest, LeaveBalance, ensure_employee_leave_balances
from payroll.models import PayrollPeriod, Payslip
from performance.models import Goal, PerformanceReview, EmployeeAward
from support.models import SupportTicket, OfficialDocumentRequest, Asset


@login_required
def smart_dashboard(request):
    """Directs each role to their authorized dashboard."""
    role = request.user.role
    if role == CustomUser.Role.HEAD or request.user.is_superuser:
        return redirect('portal:dashboard_head')
    elif role == CustomUser.Role.HR:
        return redirect('portal:dashboard_hr')
    elif role == CustomUser.Role.SITE_MANAGER:
        return redirect('portal:dashboard_site_manager')
    else:
        return redirect('portal:dashboard_employee')


@login_required
def company_home_portal(request):
    """
    Section 3: Home Page – Company Portal.
    Personalized welcome, live punch widget, holidays, events,
    birthdays with privacy, announcements, employee of the month.
    """
    today = timezone.localdate()
    user = request.user
    emp_profile = getattr(user, 'employee_profile', None)

    # 1. Today's attendance for the logged-in user
    today_attendance = None
    if emp_profile:
        today_attendance = Attendance.objects.filter(employee=emp_profile, date=today).first()

    # 2. Upcoming Holidays
    upcoming_holidays = Holiday.objects.filter(date__gte=today)[:5]

    # 3. Official Events
    upcoming_events = CompanyEvent.objects.filter(is_active=True, start_datetime__gte=timezone.now())[:4]

    # 4. Announcements
    announcements = Announcement.objects.all()[:6]

    # 5. Birthdays & Anniversaries (with Privacy check!)
    # Today's birthdays
    today_birthdays = EmployeeProfile.objects.filter(
        status='ACTIVE',
        show_birthday_publicly=True,
        date_of_birth__month=today.month,
        date_of_birth__day=today.day
    ).select_related('user', 'department')

    # Upcoming birthdays in the next 15 days
    upcoming_birthdays = []
    active_employees_with_dob = EmployeeProfile.objects.filter(
        status='ACTIVE',
        show_birthday_publicly=True,
        date_of_birth__isnull=False
    ).exclude(date_of_birth__month=today.month, date_of_birth__day=today.day).select_related('user', 'department')

    for emp in active_employees_with_dob:
        # Check if birthday falls in next 15 days
        try:
            bday_this_year = date(today.year, emp.date_of_birth.month, emp.date_of_birth.day)
            diff = (bday_this_year - today).days
            if 0 < diff <= 15:
                upcoming_birthdays.append((emp, diff, bday_this_year))
        except ValueError:
            pass
    upcoming_birthdays.sort(key=lambda x: x[1])
    upcoming_birthdays = upcoming_birthdays[:5]

    # Work Anniversaries this month
    work_anniversaries = EmployeeProfile.objects.filter(
        status='ACTIVE',
        joining_date__month=today.month
    ).exclude(joining_date__year=today.year).select_related('user', 'department')[:5]

    # 6. Employee of the Month / Featured Awards
    featured_awards = EmployeeAward.objects.filter(is_featured=True).select_related('employee__user', 'employee__department')[:2]

    # 7. Quick stats for user
    leave_balances = []
    if emp_profile:
        ensure_employee_leave_balances(emp_profile, today.year)
        leave_balances = LeaveBalance.objects.filter(employee=emp_profile, year=today.year, leave_type__code__in=['SL', 'PL']).select_related('leave_type')

    return render(request, 'portal/home.html', {
        'emp_profile': emp_profile,
        'today_attendance': today_attendance,
        'upcoming_holidays': upcoming_holidays,
        'upcoming_events': upcoming_events,
        'announcements': announcements,
        'today_birthdays': today_birthdays,
        'upcoming_birthdays': upcoming_birthdays,
        'work_anniversaries': work_anniversaries,
        'featured_awards': featured_awards,
        'leave_balances': leave_balances,
        'today': today,
    })


# -------------------------------------------------------------------------
# AUTHORITY 1: EMPLOYEE DASHBOARD
# -------------------------------------------------------------------------
@login_required
def dashboard_employee(request):
    user = request.user
    emp_profile = getattr(user, 'employee_profile', None)
    today = timezone.localdate()

    if not emp_profile:
        messages.warning(request, "Employee profile not found. Please contact HR.")
        return redirect('portal:home')

    # Today's attendance
    today_attendance = Attendance.objects.filter(employee=emp_profile, date=today).first()

    # Leave balances for this year (Sick Leave & Paid Leave)
    ensure_employee_leave_balances(emp_profile, today.year)
    leave_balances = LeaveBalance.objects.filter(employee=emp_profile, year=today.year, leave_type__code__in=['SL', 'PL']).select_related('leave_type')

    # Recent leave requests
    my_leaves = LeaveRequest.objects.filter(employee=emp_profile).select_related('leave_type')[:5]

    # Recent attendance (last 7 days)
    recent_attendance = Attendance.objects.filter(employee=emp_profile).order_by('-date')[:7]

    # Assigned goals
    my_goals = Goal.objects.filter(employee=emp_profile).order_by('-created_at')[:4]

    # Latest payslip
    latest_payslip = Payslip.objects.filter(employee=emp_profile).order_by('-year', '-month').first()

    # Open support tickets
    open_tickets = SupportTicket.objects.filter(employee=emp_profile).exclude(status='CLOSED')[:4]

    return render(request, 'portal/dashboard_employee.html', {
        'profile': emp_profile,
        'today_attendance': today_attendance,
        'leave_balances': leave_balances,
        'my_leaves': my_leaves,
        'recent_attendance': recent_attendance,
        'my_goals': my_goals,
        'latest_payslip': latest_payslip,
        'open_tickets': open_tickets,
        'today': today,
    })


# -------------------------------------------------------------------------
# AUTHORITY 2: HR DASHBOARD
# -------------------------------------------------------------------------
@login_required
@hr_required
def dashboard_hr(request):
    today = timezone.localdate()

    # Workforce counts
    total_employees = EmployeeProfile.objects.count()
    active_employees = EmployeeProfile.objects.filter(status='ACTIVE').count()
    new_joiners_month = EmployeeProfile.objects.filter(joining_date__month=today.month, joining_date__year=today.year).count()

    # Today's attendance across all employees
    present_today = Attendance.objects.filter(date=today, status='PRESENT').count()
    half_day_today = Attendance.objects.filter(date=today, status='HALF_DAY').count()
    on_leave_today = Attendance.objects.filter(date=today, status='ON_LEAVE').count()
    late_today = Attendance.objects.filter(date=today, is_late=True).count()
    absent_today = max(0, active_employees - present_today - half_day_today - on_leave_today)

    # Pending Action Queues
    pending_leaves = LeaveRequest.objects.filter(status__in=[LeaveRequest.Status.PENDING_HR, LeaveRequest.Status.PENDING_MANAGER]).select_related('employee__user', 'leave_type')[:6]
    pending_corrections = AttendanceCorrectionRequest.objects.filter(status='PENDING').select_related('employee__user')[:5]
    pending_profile_requests = ProfileCorrectionRequest.objects.filter(status='PENDING').select_related('employee__user')[:5]
    pending_doc_requests = OfficialDocumentRequest.objects.filter(status='PENDING').select_related('employee__user')[:5]

    # Department breakdown for chart
    dept_stats = Department.objects.annotate(emp_count=Count('employees')).values('name', 'emp_count')

    # Latest Payroll Status
    latest_payroll = PayrollPeriod.objects.order_by('-year', '-month').first()

    return render(request, 'portal/dashboard_hr.html', {
        'total_employees': total_employees,
        'active_employees': active_employees,
        'new_joiners_month': new_joiners_month,
        'present_today': present_today,
        'absent_today': absent_today,
        'half_day_today': half_day_today,
        'on_leave_today': on_leave_today,
        'late_today': late_today,
        'pending_leaves': pending_leaves,
        'pending_corrections': pending_corrections,
        'pending_profile_requests': pending_profile_requests,
        'pending_doc_requests': pending_doc_requests,
        'dept_stats': list(dept_stats),
        'latest_payroll': latest_payroll,
        'today': today,
    })


# -------------------------------------------------------------------------
# AUTHORITY 3: SITE MANAGER DASHBOARD
# -------------------------------------------------------------------------
@login_required
@site_manager_required
def dashboard_site_manager(request):
    today = timezone.localdate()
    user = request.user

    # Find sites managed by this user
    if user.is_head_role or user.is_hr_role:
        # If head/hr inspects site manager dashboard, show default site
        managed_sites = Site.objects.filter(is_active=True)
    else:
        managed_sites = Site.objects.filter(site_manager=user)

    current_site = managed_sites.first()

    site_employees = EmployeeProfile.objects.filter(site__in=managed_sites, status='ACTIVE').select_related('user', 'designation', 'department')
    total_site_employees = site_employees.count()

    # Today's attendance for this site
    site_emp_ids = site_employees.values_list('id', flat=True)
    present_today = Attendance.objects.filter(employee__id__in=site_emp_ids, date=today, status='PRESENT').count()
    late_today = Attendance.objects.filter(employee__id__in=site_emp_ids, date=today, is_late=True).count()
    on_leave_today = Attendance.objects.filter(employee__id__in=site_emp_ids, date=today, status='ON_LEAVE').count()
    absent_today = max(0, total_site_employees - present_today - on_leave_today)

    attendance_pct = round((present_today / total_site_employees * 100), 1) if total_site_employees > 0 else 0

    # Team leave requests awaiting site manager review
    team_leave_requests = LeaveRequest.objects.filter(
        employee__id__in=site_emp_ids,
        status=LeaveRequest.Status.PENDING_MANAGER
    ).select_related('employee__user', 'leave_type')

    # Team attendance corrections awaiting review
    team_corrections = AttendanceCorrectionRequest.objects.filter(
        employee__id__in=site_emp_ids,
        status='PENDING'
    ).select_related('employee__user')

    # Site specific announcements
    site_announcements = Announcement.objects.filter(
        Q(target_site=current_site) | Q(target_site__isnull=True)
    )[:4]

    return render(request, 'portal/dashboard_site_manager.html', {
        'current_site': current_site,
        'managed_sites': managed_sites,
        'total_site_employees': total_site_employees,
        'present_today': present_today,
        'late_today': late_today,
        'on_leave_today': on_leave_today,
        'absent_today': absent_today,
        'attendance_pct': attendance_pct,
        'site_employees': site_employees[:10],
        'team_leave_requests': team_leave_requests,
        'team_corrections': team_corrections,
        'site_announcements': site_announcements,
        'today': today,
    })


# -------------------------------------------------------------------------
# AUTHORITY 4: HEAD / SUPER ADMIN DASHBOARD
# -------------------------------------------------------------------------
@login_required
@head_required
def dashboard_head(request):
    today = timezone.localdate()

    # Executive Organization-Wide Overview
    total_workforce = EmployeeProfile.objects.count()
    active_workforce = EmployeeProfile.objects.filter(status='ACTIVE').count()
    sites_count = Site.objects.filter(is_active=True).count()
    departments_count = Department.objects.count()

    # Today's Global Attendance
    present_today = Attendance.objects.filter(date=today, status='PRESENT').count()
    on_leave_today = Attendance.objects.filter(date=today, status='ON_LEAVE').count()
    absent_today = max(0, active_workforce - present_today - on_leave_today)

    # Monthly Payroll Expenditure
    latest_payrolls = PayrollPeriod.objects.order_by('-year', '-month')[:6]
    payroll_payout_total = latest_payrolls.first().total_net if latest_payrolls.exists() else Decimal('0.00')

    # Management Approvals Queue
    pending_payroll_approvals = PayrollPeriod.objects.filter(status='SUBMITTED')
    high_level_leaves = LeaveRequest.objects.filter(status__in=[LeaveRequest.Status.PENDING_HR, LeaveRequest.Status.PENDING_MANAGER]).select_related('employee__user', 'leave_type')[:5]

    # Department and Site Distributions for Charts
    dept_distribution = Department.objects.annotate(total=Count('employees')).values('name', 'total')
    site_distribution = Site.objects.annotate(total=Count('employees')).values('name', 'total')

    # Recent System Audit Logs
    recent_audit_logs = AuditLog.objects.select_related('user')[:8]

    return render(request, 'portal/dashboard_head.html', {
        'total_workforce': total_workforce,
        'active_workforce': active_workforce,
        'sites_count': sites_count,
        'departments_count': departments_count,
        'present_today': present_today,
        'absent_today': absent_today,
        'on_leave_today': on_leave_today,
        'payroll_payout_total': payroll_payout_total,
        'latest_payrolls': latest_payrolls,
        'pending_payroll_approvals': pending_payroll_approvals,
        'high_level_leaves': high_level_leaves,
        'dept_distribution': list(dept_distribution),
        'site_distribution': list(site_distribution),
        'recent_audit_logs': recent_audit_logs,
        'today': today,
    })


# -------------------------------------------------------------------------
# EVENTS, HOLIDAYS & POLICIES
# -------------------------------------------------------------------------
@login_required
def events_list(request):
    events = CompanyEvent.objects.filter(is_active=True).order_by('start_datetime')
    registered_ids = EventParticipant.objects.filter(user=request.user).values_list('event_id', flat=True)
    return render(request, 'portal/events_list.html', {
        'events': events,
        'registered_ids': list(registered_ids)
    })


@login_required
def register_event(request, event_id):
    event = get_object_or_404(CompanyEvent, id=event_id, is_active=True)
    participant, created = EventParticipant.objects.get_or_create(event=event, user=request.user)
    if created:
        messages.success(request, f"You have successfully registered for {event.title}!")
    else:
        messages.info(request, f"You are already registered for {event.title}.")
    return redirect('portal:events_list')


@login_required
def holidays_list(request):
    year = request.GET.get('year', timezone.localdate().year)
    holidays = Holiday.objects.filter(date__year=year).order_by('date')
    return render(request, 'portal/holidays_list.html', {
        'holidays': holidays,
        'selected_year': int(year)
    })


@login_required
def policies_list(request):
    policies = CompanyPolicy.objects.all().order_by('-effective_date')
    acknowledged_ids = request.user.policy_acknowledgements.values_list('policy_id', flat=True)
    return render(request, 'portal/policies_list.html', {
        'policies': policies,
        'acknowledged_ids': list(acknowledged_ids)
    })


@login_required
def acknowledge_policy(request, policy_id):
    from organization.models import PolicyAcknowledgement
    policy = get_object_or_404(CompanyPolicy, id=policy_id)
    PolicyAcknowledgement.objects.get_or_create(policy=policy, user=request.user)
    messages.success(request, f"Policy '{policy.title}' acknowledged successfully.")
    return redirect('portal:policies_list')
