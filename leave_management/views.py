from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from accounts.decorators import role_required, hr_required, site_manager_required, log_audit_trail
from accounts.models import CustomUser
from leave_management.models import LeaveRequest, LeaveBalance, LeaveType
from leave_management.forms import LeaveApplicationForm
from attendance.models import Attendance
from notifications.models import create_notification


@login_required
def apply_leave(request):
    """Employee applies for leave with balance check and workflow routing."""
    emp = getattr(request.user, 'employee_profile', None)
    if not emp:
        messages.error(request, "Employee profile required to apply for leave.")
        return redirect('portal:smart_dashboard')

    today = timezone.localdate()
    balances = LeaveBalance.objects.filter(employee=emp, year=today.year).select_related('leave_type')

    if request.method == 'POST':
        form = LeaveApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            leave_req = form.save(commit=False)
            leave_req.employee = emp

            start = leave_req.start_date
            end = leave_req.end_date

            if end < start:
                messages.error(request, "End date cannot be earlier than start date.")
                return render(request, 'leave_management/apply_leave.html', {'form': form, 'balances': balances})

            # Calculate total days (excluding Sundays)
            curr = start
            working_days_count = 0
            while curr <= end:
                if curr.weekday() != 6: # Not Sunday
                    working_days_count += 1
                curr += timedelta(days=1)

            if working_days_count == 0:
                messages.error(request, "Selected date range contains no working days.")
                return render(request, 'leave_management/apply_leave.html', {'form': form, 'balances': balances})

            if leave_req.is_half_day:
                total_days = Decimal('0.5')
            else:
                total_days = Decimal(str(working_days_count))

            leave_req.total_days = total_days

            # Balance check for paid leave types
            if leave_req.leave_type.is_paid:
                bal = LeaveBalance.objects.filter(employee=emp, leave_type=leave_req.leave_type, year=start.year).first()
                if not bal or bal.available_days < total_days:
                    available = bal.available_days if bal else 0
                    messages.error(request, f"Insufficient {leave_req.leave_type.name} balance. Available: {available} days, Requested: {total_days} days.")
                    return render(request, 'leave_management/apply_leave.html', {'form': form, 'balances': balances})

            leave_req.status = LeaveRequest.Status.PENDING_MANAGER
            leave_req.save()

            # Update pending days in balance
            if leave_req.leave_type.is_paid:
                bal = LeaveBalance.objects.filter(employee=emp, leave_type=leave_req.leave_type, year=start.year).first()
                if bal:
                    bal.pending_days += total_days
                    bal.save()

            # Notify Site Manager or HR
            mgr = emp.reporting_manager or (emp.site.site_manager if emp.site else None)
            if mgr:
                create_notification(
                    recipient=mgr,
                    title='New Leave Application',
                    message=f"{emp.full_name} applied for {total_days} days {leave_req.leave_type.code} ({start} to {end}).",
                    notification_type='LEAVE',
                    target_url='/leave/requests/'
                )

            log_audit_trail('CREATE', 'Leave Management', f"Leave applied by {emp.emp_id} ({total_days} days {leave_req.leave_type.code})", user=request.user)
            messages.success(request, f"Leave application for {total_days} days submitted successfully!")
            return redirect('leave_management:my_leaves')
    else:
        form = LeaveApplicationForm()

    return render(request, 'leave_management/apply_leave.html', {
        'form': form,
        'balances': balances,
        'employee': emp,
    })


@login_required
def my_leaves(request):
    """View leave history and balances for logged-in employee."""
    emp = getattr(request.user, 'employee_profile', None)
    if not emp:
        messages.error(request, "Employee profile required.")
        return redirect('portal:home')

    today = timezone.localdate()
    balances = LeaveBalance.objects.filter(employee=emp, year=today.year).select_related('leave_type')
    leave_requests = LeaveRequest.objects.filter(employee=emp).select_related('leave_type', 'manager_action_by', 'hr_action_by').order_by('-applied_at')

    return render(request, 'leave_management/my_leaves.html', {
        'employee': emp,
        'balances': balances,
        'leave_requests': leave_requests,
    })


@login_required
def cancel_leave(request, request_id):
    """Employee cancels a pending leave request."""
    emp = getattr(request.user, 'employee_profile', None)
    leave_req = get_object_or_404(LeaveRequest, id=request_id, employee=emp)

    if leave_req.status not in [LeaveRequest.Status.PENDING_MANAGER, LeaveRequest.Status.PENDING_HR]:
        messages.error(request, "Only pending leave requests can be cancelled.")
        return redirect('leave_management:my_leaves')

    leave_req.status = LeaveRequest.Status.CANCELLED
    leave_req.save()

    # Revert pending balance
    if leave_req.leave_type.is_paid:
        bal = LeaveBalance.objects.filter(employee=emp, leave_type=leave_req.leave_type, year=leave_req.start_date.year).first()
        if bal:
            bal.pending_days = max(Decimal('0.0'), bal.pending_days - leave_req.total_days)
            bal.save()

    messages.info(request, "Your leave application has been cancelled.")
    return redirect('leave_management:my_leaves')


@login_required
@role_required([CustomUser.Role.HR, CustomUser.Role.HEAD, CustomUser.Role.SITE_MANAGER])
def leave_requests_admin(request):
    """
    Queue of leave requests for Site Managers and HR Administrators.
    Strict RBAC: Site Managers see requests from their site. HR & Head see all.
    """
    user = request.user
    status_filter = request.GET.get('status', '')

    queryset = LeaveRequest.objects.select_related('employee__user', 'employee__site', 'employee__department', 'leave_type').all()

    if user.is_site_manager_role and not (user.is_hr_role or user.is_head_role):
        queryset = queryset.filter(employee__site__in=user.managed_sites.all())

    if status_filter:
        queryset = queryset.filter(status=status_filter)

    return render(request, 'leave_management/admin_queue.html', {
        'leave_requests': queryset,
        'selected_status': status_filter,
    })


@login_required
@role_required([CustomUser.Role.HR, CustomUser.Role.HEAD, CustomUser.Role.SITE_MANAGER])
def process_leave(request, request_id):
    """
    Multi-level approval workflow:
    - Site Manager recommends or rejects.
    - HR or Head provides final approval or rejection.
    """
    user = request.user
    leave_req = get_object_or_404(LeaveRequest, id=request_id)
    action = request.POST.get('action') # APPROVE, RECOMMEND, REJECT
    remarks = request.POST.get('remarks', '')

    emp = leave_req.employee

    if action == 'RECOMMEND' and (user.is_site_manager_role or user.is_hr_role or user.is_head_role):
        leave_req.manager_decision = 'RECOMMENDED'
        leave_req.manager_remarks = remarks
        leave_req.manager_action_by = user
        leave_req.manager_action_at = timezone.now()
        leave_req.status = LeaveRequest.Status.PENDING_HR
        leave_req.save()

        # Notify HR
        create_notification(
            recipient=emp.user,
            title='Leave Recommended by Manager',
            message=f"Your {leave_req.leave_type.code} request has been recommended by {user.get_full_name()} and forwarded to HR.",
            notification_type='LEAVE',
            target_url='/leave/my/'
        )
        messages.success(request, f"Leave request for {emp.full_name} recommended and forwarded to HR.")

    elif action == 'APPROVE' and (user.is_hr_role or user.is_head_role or user.is_superuser):
        leave_req.hr_decision = 'APPROVED'
        leave_req.hr_remarks = remarks
        leave_req.hr_action_by = user
        leave_req.hr_action_at = timezone.now()
        leave_req.status = LeaveRequest.Status.APPROVED
        leave_req.save()

        # Adjust balance: deduct pending and increase used
        if leave_req.leave_type.is_paid:
            bal = LeaveBalance.objects.filter(employee=emp, leave_type=leave_req.leave_type, year=leave_req.start_date.year).first()
            if bal:
                bal.pending_days = max(Decimal('0.0'), bal.pending_days - leave_req.total_days)
                bal.used_days += leave_req.total_days
                bal.save()

        # Mark Attendance records as ON_LEAVE
        curr = leave_req.start_date
        while curr <= leave_req.end_date:
            if curr.weekday() != 6:
                Attendance.objects.update_or_create(
                    employee=emp,
                    date=curr,
                    defaults={'status': 'HALF_DAY' if leave_req.is_half_day else 'ON_LEAVE', 'notes': f"Approved {leave_req.leave_type.name}"}
                )
            curr += timedelta(days=1)

        create_notification(
            recipient=emp.user,
            title='🎉 Leave Request Approved!',
            message=f"Your {leave_req.leave_type.name} application ({leave_req.start_date} to {leave_req.end_date}) has been approved.",
            notification_type='LEAVE',
            target_url='/leave/my/'
        )
        log_audit_trail('APPROVAL', 'Leave Management', f"Leave approved for {emp.emp_id} by {user.username}", user=user)
        messages.success(request, f"Leave application for {emp.full_name} has been approved.")

    elif action == 'REJECT':
        leave_req.status = LeaveRequest.Status.REJECTED
        if user.is_site_manager_role:
            leave_req.manager_decision = 'REJECTED'
            leave_req.manager_remarks = remarks
            leave_req.manager_action_by = user
            leave_req.manager_action_at = timezone.now()
        else:
            leave_req.hr_decision = 'REJECTED'
            leave_req.hr_remarks = remarks
            leave_req.hr_action_by = user
            leave_req.hr_action_at = timezone.now()
        leave_req.save()

        # Revert pending balance
        if leave_req.leave_type.is_paid:
            bal = LeaveBalance.objects.filter(employee=emp, leave_type=leave_req.leave_type, year=leave_req.start_date.year).first()
            if bal:
                bal.pending_days = max(Decimal('0.0'), bal.pending_days - leave_req.total_days)
                bal.save()

        create_notification(
            recipient=emp.user,
            title='Leave Request Rejected',
            message=f"Your {leave_req.leave_type.name} application was rejected. Reason: {remarks}",
            notification_type='LEAVE',
            target_url='/leave/my/'
        )
        messages.info(request, f"Leave request for {emp.full_name} has been rejected.")

    return redirect('leave_management:admin_queue')


@login_required
def leave_calendar_view(request):
    """Company-wide leave calendar."""
    today = timezone.localdate()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    approved_leaves = LeaveRequest.objects.filter(
        status=LeaveRequest.Status.APPROVED,
        start_date__year=year,
        start_date__month=month
    ).select_related('employee__user', 'employee__department', 'leave_type')

    return render(request, 'leave_management/calendar.html', {
        'approved_leaves': approved_leaves,
        'selected_month': month,
        'selected_year': year,
    })
