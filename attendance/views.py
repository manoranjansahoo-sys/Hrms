from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from django.core.paginator import Paginator
from accounts.models import CustomUser
from accounts.decorators import role_required, hr_required, site_manager_required, log_audit_trail
from attendance.models import Attendance, Shift, AttendanceCorrectionRequest, AttendanceAuditLog
from employees.models import EmployeeProfile
from organization.models import Department, Site
from notifications.models import create_notification


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or '127.0.0.1'


@login_required
def punch_in_view(request):
    """Self-service Punch In with server-side validation and timestamp."""
    emp = getattr(request.user, 'employee_profile', None)
    if not emp:
        messages.error(request, "Employee profile required for attendance check-in.")
        return redirect('portal:smart_dashboard')

    today = timezone.localdate()
    now = timezone.now()
    client_ip = get_client_ip(request)

    # Check existing attendance
    att = Attendance.objects.filter(employee=emp, date=today).first()
    if att:
        if att.punch_out:
            messages.warning(
                request,
                f"You have already punched out for today at {timezone.localtime(att.punch_out).strftime('%I:%M %p')}. "
                "Only one punch-in and punch-out is allowed per day."
            )
            return redirect(request.META.get('HTTP_REFERER', 'portal:smart_dashboard'))
        if att.punch_in:
            messages.warning(
                request,
                f"You are already punched in today at {timezone.localtime(att.punch_in).strftime('%I:%M %p')}."
            )
            return redirect(request.META.get('HTTP_REFERER', 'portal:smart_dashboard'))
    else:
        att = Attendance(employee=emp, date=today)

    # Determine office schedule (Standard 9:30 AM to 6:30 PM, no multi-shifts)
    shift = Shift.objects.filter(is_default=True).first() or Shift.objects.first()
    if not shift:
        shift, _ = Shift.objects.get_or_create(
            name='Office Hours',
            defaults={
                'start_time': time(9, 30),
                'end_time': time(18, 30),
                'grace_period_minutes': 0,
                'full_day_hours': Decimal('8.00'),
                'half_day_hours': Decimal('4.50'),
                'is_default': True,
            }
        )
    att.shift = shift
    att.punch_in = now
    att.punch_in_ip = client_ip
    att.device_source = 'WEB'
    att.status = 'PRESENT'

    # Check late arrival (Office opens at 9:30 AM)
    start_time_val = shift.start_time if shift else time(9, 30)
    grace_min = shift.grace_period_minutes if shift else 0
    grace_time = (datetime.combine(today, start_time_val) + timedelta(minutes=grace_min)).time()
    if timezone.localtime(now).time() > grace_time:
        att.is_late = True

    att.save()
    log_audit_trail('CREATE', 'Attendance', f"Punch-in recorded for {emp.emp_id} at {now.strftime('%H:%M:%S')}", user=request.user, ip_address=client_ip)
    messages.success(request, f"Punch In successful at {timezone.localtime(now).strftime('%I:%M %p')}! Have a productive day.")
    return redirect(request.META.get('HTTP_REFERER', 'portal:smart_dashboard'))


@login_required
def punch_out_view(request):
    """Self-service Punch Out with automatic working hours and overtime calculation."""
    emp = getattr(request.user, 'employee_profile', None)
    if not emp:
        messages.error(request, "Employee profile required.")
        return redirect('portal:smart_dashboard')

    today = timezone.localdate()
    now = timezone.now()
    client_ip = get_client_ip(request)

    att = Attendance.objects.filter(employee=emp, date=today).first()
    if not att or not att.punch_in:
        messages.error(request, "You have not punched in today yet! Punch in is required before you can punch out.")
        return redirect(request.META.get('HTTP_REFERER', 'portal:smart_dashboard'))

    if att.punch_out:
        messages.warning(
            request,
            f"You have already punched out today at {timezone.localtime(att.punch_out).strftime('%I:%M %p')}. "
            "Only one punch-out is permitted per day."
        )
        return redirect(request.META.get('HTTP_REFERER', 'portal:smart_dashboard'))

    att.punch_out = now
    att.punch_out_ip = client_ip
    att.calculate_hours()
    att.save()

    log_audit_trail('UPDATE', 'Attendance', f"Punch-out recorded for {emp.emp_id}. Total hours: {att.working_hours}", user=request.user, ip_address=client_ip)
    messages.success(request, f"Punch Out successful at {timezone.localtime(now).strftime('%I:%M %p')}. Total working hours today: {att.working_hours} hrs.")
    return redirect(request.META.get('HTTP_REFERER', 'portal:smart_dashboard'))


@login_required
def my_attendance(request):
    """Monthly attendance calendar & punch history for logged-in employee."""
    emp = getattr(request.user, 'employee_profile', None)
    if not emp:
        messages.error(request, "Employee profile not found.")
        return redirect('portal:home')

    today = timezone.localdate()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    attendances = Attendance.objects.filter(
        employee=emp,
        date__year=year,
        date__month=month
    ).order_by('-date')

    # Monthly Summary Stats
    total_present = attendances.filter(status='PRESENT').count()
    total_half_day = attendances.filter(status='HALF_DAY').count()
    total_late = attendances.filter(is_late=True).count()
    total_hours = sum(a.working_hours for a in attendances)
    total_ot = sum(a.overtime_hours for a in attendances)

    my_corrections = AttendanceCorrectionRequest.objects.filter(employee=emp).order_by('-created_at')[:5]

    return render(request, 'attendance/my_attendance.html', {
        'employee': emp,
        'attendances': attendances,
        'selected_month': month,
        'selected_year': year,
        'total_present': total_present,
        'total_half_day': total_half_day,
        'total_late': total_late,
        'total_hours': total_hours,
        'total_ot': total_ot,
        'my_corrections': my_corrections,
    })


@login_required
def request_attendance_correction(request):
    """Employee submits correction for a missing punch or incorrect timing."""
    emp = getattr(request.user, 'employee_profile', None)
    if not emp:
        messages.error(request, "Employee profile required.")
        return redirect('portal:home')

    if request.method == 'POST':
        req_date_str = request.POST.get('date')
        in_time_str = request.POST.get('punch_in')
        out_time_str = request.POST.get('punch_out')
        reason = request.POST.get('reason', '')

        try:
            req_date = datetime.strptime(req_date_str, '%Y-%m-%d').date()
            pin_dt = None
            pout_dt = None
            if in_time_str:
                pin_time = datetime.strptime(in_time_str, '%H:%M').time()
                pin_dt = timezone.make_aware(datetime.combine(req_date, pin_time))
            if out_time_str:
                pout_time = datetime.strptime(out_time_str, '%H:%M').time()
                pout_dt = timezone.make_aware(datetime.combine(req_date, pout_time))

            att = Attendance.objects.filter(employee=emp, date=req_date).first()

            corr = AttendanceCorrectionRequest.objects.create(
                employee=emp,
                attendance=att,
                date=req_date,
                requested_punch_in=pin_dt,
                requested_punch_out=pout_dt,
                reason=reason,
                status='PENDING'
            )

            # Notify reporting manager or HR
            mgr = emp.reporting_manager
            if mgr:
                create_notification(
                    recipient=mgr,
                    title='Attendance Correction Request',
                    message=f"{emp.full_name} ({emp.emp_id}) requested attendance adjustment for {req_date}.",
                    notification_type='ATTENDANCE',
                    target_url='/attendance/corrections/'
                )

            messages.success(request, f"Attendance correction request for {req_date} has been submitted for approval.")
            return redirect('attendance:my_attendance')
        except Exception as e:
            messages.error(request, f"Error submitting request: {str(e)}")

    return render(request, 'attendance/correction_form.html', {'employee': emp})


@login_required
@role_required([CustomUser.Role.HR, CustomUser.Role.HEAD, CustomUser.Role.SITE_MANAGER])
def attendance_admin_register(request):
    """
    Daily / Monthly attendance register for administrators and managers.
    Filter by date, department, and site.
    """
    user = request.user
    selected_date_str = request.GET.get('date', timezone.localdate().strftime('%Y-%m-%d'))
    try:
        selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.localdate()

    dept_id = request.GET.get('department', '')
    site_id = request.GET.get('site', '')

    employees = EmployeeProfile.objects.filter(status='ACTIVE').select_related('user', 'department', 'site')

    # If Site Manager, filter to their managed site
    if user.is_site_manager_role and not (user.is_hr_role or user.is_head_role):
        employees = employees.filter(site__in=user.managed_sites.all())
    elif site_id:
        employees = employees.filter(site_id=site_id)

    if dept_id:
        employees = employees.filter(department_id=dept_id)

    # Attach attendance record for each employee on the selected date
    attendance_records = {
        att.employee_id: att
        for att in Attendance.objects.filter(date=selected_date, employee__in=employees).select_related('shift')
    }

    roster = []
    present_cnt = 0
    absent_cnt = 0
    leave_cnt = 0
    late_cnt = 0

    for emp in employees:
        att = attendance_records.get(emp.id)
        if att:
            if att.status == 'PRESENT':
                present_cnt += 1
            elif att.status == 'ON_LEAVE':
                leave_cnt += 1
            if att.is_late:
                late_cnt += 1
        else:
            absent_cnt += 1
        roster.append({'employee': emp, 'attendance': att})

    departments = Department.objects.all()
    sites = Site.objects.filter(is_active=True)

    return render(request, 'attendance/admin_register.html', {
        'selected_date': selected_date,
        'roster': roster,
        'departments': departments,
        'sites': sites,
        'selected_dept': dept_id,
        'selected_site': site_id,
        'present_cnt': present_cnt,
        'absent_cnt': absent_cnt,
        'leave_cnt': leave_cnt,
        'late_cnt': late_cnt,
    })


@login_required
@role_required([CustomUser.Role.HR, CustomUser.Role.HEAD, CustomUser.Role.SITE_MANAGER])
def employee_attendance_detail(request, emp_id):
    """
    Comprehensive attendance history and drill-down logs for a specific employee.
    Accessible to HR, Company Head, and Site Managers.
    """
    user = request.user
    emp = get_object_or_404(
        EmployeeProfile.objects.select_related('user', 'department', 'site', 'designation', 'reporting_manager'),
        emp_id=emp_id
    )

    # Site managers can only view staff assigned to their managed sites
    if user.is_site_manager_role and not (user.is_hr_role or user.is_head_role):
        if not user.managed_sites.filter(id=emp.site_id).exists():
            messages.error(request, "You do not have permission to view attendance records for this employee.")
            return redirect('attendance:admin_register')

    now = timezone.localtime(timezone.now())
    view_all = request.GET.get('view_all', '0') == '1'

    month_str = request.GET.get('month')
    year_str = request.GET.get('year')

    try:
        month = int(month_str) if month_str else now.month
        year = int(year_str) if year_str else now.year
    except (ValueError, TypeError):
        month = now.month
        year = now.year

    attendances_qs = Attendance.objects.filter(employee=emp).select_related('shift').order_by('-date')

    if not view_all:
        attendances = attendances_qs.filter(date__year=year, date__month=month)
    else:
        attendances = attendances_qs

    # Summary Stats
    total_records = attendances.count()
    total_present = attendances.filter(status='PRESENT').count()
    total_half_day = attendances.filter(status='HALF_DAY').count()
    total_leave = attendances.filter(status='ON_LEAVE').count()
    total_absent = attendances.filter(status='ABSENT').count()
    total_late = attendances.filter(is_late=True).count()
    total_hours = sum((a.working_hours or Decimal('0.00')) for a in attendances)
    total_ot = sum((a.overtime_hours or Decimal('0.00')) for a in attendances)

    # Monthly quick switcher (past 6 months)
    recent_months = []
    curr_date = date(now.year, now.month, 1)
    for i in range(6):
        m_year = curr_date.year
        m_month = curr_date.month - i
        while m_month <= 0:
            m_month += 12
            m_year -= 1
        m_date = date(m_year, m_month, 1)
        recent_months.append({
            'month': m_month,
            'year': m_year,
            'label': m_date.strftime('%B %Y'),
            'short_label': m_date.strftime('%b %Y'),
            'is_selected': (not view_all and m_month == month and m_year == year)
        })

    # Recent correction requests
    corrections = AttendanceCorrectionRequest.objects.filter(employee=emp).order_by('-date')[:10]

    return render(request, 'attendance/employee_attendance_detail.html', {
        'employee': emp,
        'attendances': attendances,
        'total_records': total_records,
        'selected_month': month,
        'selected_year': year,
        'view_all': view_all,
        'total_present': total_present,
        'total_half_day': total_half_day,
        'total_leave': total_leave,
        'total_absent': total_absent,
        'total_late': total_late,
        'total_hours': total_hours,
        'total_ot': total_ot,
        'recent_months': recent_months,
        'corrections': corrections,
    })


@login_required
@role_required([CustomUser.Role.HR, CustomUser.Role.HEAD, CustomUser.Role.SITE_MANAGER])
def attendance_corrections_list(request):
    """View and approve/reject attendance corrections."""
    user = request.user
    corrections = AttendanceCorrectionRequest.objects.select_related('employee__user', 'employee__site', 'attendance').all()

    if user.is_site_manager_role and not (user.is_hr_role or user.is_head_role):
        corrections = corrections.filter(employee__site__in=user.managed_sites.all())

    return render(request, 'attendance/corrections_list.html', {'corrections': corrections})


@login_required
@role_required([CustomUser.Role.HR, CustomUser.Role.HEAD, CustomUser.Role.SITE_MANAGER])
def approve_attendance_correction(request, request_id):
    """Approve or reject attendance correction."""
    corr = get_object_or_404(AttendanceCorrectionRequest, id=request_id)
    action = request.POST.get('action')
    notes = request.POST.get('notes', '')

    if action == 'APPROVE':
        corr.status = 'APPROVED'
        corr.reviewed_by = request.user
        corr.reviewed_at = timezone.now()
        corr.review_notes = notes
        corr.save()

        # Update or create Attendance record
        att, created = Attendance.objects.get_or_create(
            employee=corr.employee,
            date=corr.date,
            defaults={'status': 'PRESENT', 'device_source': 'MANUAL'}
        )
        if corr.requested_punch_in:
            att.punch_in = corr.requested_punch_in
        if corr.requested_punch_out:
            att.punch_out = corr.requested_punch_out

        att.calculate_hours()
        att.save()

        # Audit log
        AttendanceAuditLog.objects.create(
            attendance=att,
            action='CORRECTION_APPROVED',
            changed_by=request.user,
            reason=corr.reason
        )

        create_notification(
            recipient=corr.employee.user,
            title='Attendance Correction Approved',
            message=f"Your attendance correction request for {corr.date} has been approved.",
            notification_type='ATTENDANCE',
            target_url='/attendance/my/'
        )

        messages.success(request, f"Attendance correction for {corr.employee.full_name} has been approved.")
    elif action == 'REJECT':
        corr.status = 'REJECTED'
        corr.reviewed_by = request.user
        corr.reviewed_at = timezone.now()
        corr.review_notes = notes
        corr.save()

        create_notification(
            recipient=corr.employee.user,
            title='Attendance Correction Rejected',
            message=f"Your attendance correction request for {corr.date} was rejected. Note: {notes}",
            notification_type='ATTENDANCE',
            target_url='/attendance/my/'
        )
        messages.info(request, f"Attendance correction for {corr.employee.full_name} has been rejected.")

    return redirect('attendance:corrections_list')
