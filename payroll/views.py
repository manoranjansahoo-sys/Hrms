from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, HttpResponseForbidden, JsonResponse
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
import calendar
from accounts.models import CustomUser
from accounts.decorators import role_required, hr_required, head_required, log_audit_trail
from payroll.models import PayrollPeriod, Payslip, SalaryStructure
from payroll.pdf_generator import generate_payslip_pdf
from payroll.calculator import compute_employee_salary, get_office_hours_and_grace, round_decimal
from payroll.reports import export_payroll_csv, export_payroll_excel, export_payroll_pdf
from employees.models import EmployeeProfile
from attendance.models import Attendance
from organization.models import Holiday, OperatingSchedule
from notifications.models import create_notification


@login_required
def my_payslips(request):
    """Employee views their personal payslip history."""
    emp = getattr(request.user, 'employee_profile', None)
    if not emp:
        messages.error(request, "Employee profile required to view payslips.")
        return redirect('portal:smart_dashboard')

    payslips = Payslip.objects.filter(employee=emp).select_related('payroll_period').order_by('-year', '-month')
    salary_struct = getattr(emp, 'salary_structure', None)

    return render(request, 'payroll/my_payslips.html', {
        'employee': emp,
        'payslips': payslips,
        'salary_struct': salary_struct,
    })


@login_required
def download_payslip_pdf(request, payslip_id):
    """
    Download official PDF payslip.
    Strict Security: Employees can ONLY download their own payslip.
    HR and Head can download any payslip.
    """
    payslip = get_object_or_404(Payslip.objects.select_related('employee__user', 'employee__department', 'employee__designation', 'employee__site', 'payroll_period'), id=payslip_id)
    user = request.user

    is_owner = (payslip.employee.user == user)
    can_download = (is_owner or user.is_hr_role or user.is_head_role or user.is_superuser)

    if not can_download:
        log_audit_trail('SECURITY', 'Payroll', f"Unauthorized attempt by {user.username} to download payslip #{payslip_id}", user=user)
        return HttpResponseForbidden("Access Denied: You do not have permission to access this confidential salary document.")

    pdf_buffer = generate_payslip_pdf(payslip)
    month_name = payslip.payroll_period.get_month_display()
    filename = f"Payslip_{payslip.employee.emp_id}_{month_name}_{payslip.year}.pdf"

    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@role_required([CustomUser.Role.HR, CustomUser.Role.HEAD])
def payroll_dashboard(request):
    """Executive & HR Payroll Administration Panel."""
    payroll_periods = PayrollPeriod.objects.select_related('processed_by', 'approved_by').order_by('-year', '-month')
    recent_period = payroll_periods.first()

    total_expenditure = sum(p.total_net for p in payroll_periods.filter(status='APPROVED'))

    return render(request, 'payroll/dashboard.html', {
        'payroll_periods': payroll_periods,
        'recent_period': recent_period,
        'total_expenditure': total_expenditure,
    })


@login_required
@hr_required
def generate_payroll_period(request):
    """
    Generates a new monthly payroll period based on the Unified Master Formula:
    Base Rates:
      - Per-Day Rate = Base Salary / 30
      - Required Daily Hours = Office End - Office Start
      - Per-Minute Rate = Per-Day Rate / (Required Daily Hours * 60)
    Part A (Leave & Absence):
      - Exclude Public Holidays (Holiday calendar) and Weekly Offs (Sundays)
      - Excess SL = max(0, Approved SL - SL Limit)
      - Excess CL = max(0, Approved CL - CL Limit)
      - Unexcused Absences = Working days with no check-in & no approved leave
      - Leave Deduction = (Excess SL + Excess CL + Unexcused Absences) * Per-Day Rate
    Part B (Late & Overtime Shortfall):
      - Late minutes beyond grace period
      - Overtime minutes beyond shift end
      - Net Shortfall = max(0, Late - OT) if OT compensation enabled
      - Shortfall Deduction = Net Shortfall * Per-Minute Rate
    Part C (Gross Deduction & HR Condone):
      - Gross Deduction = Leave Deduction + Shortfall Deduction
      - Final Deduction = max(0, Gross Deduction - HR Condone)
      - Net Payable = max(0, Base Salary - Final Deduction)
    """
    today = timezone.localdate()

    if request.method == 'POST':
        month = int(request.POST.get('month', today.month))
        year = int(request.POST.get('year', today.year))
        allow_ot = (request.POST.get('allow_ot', 'on') in ['on', 'true', '1'])

        # Check if already exists
        if PayrollPeriod.objects.filter(month=month, year=year).exists():
            messages.warning(request, f"Payroll for {calendar.month_name[month]} {year} already exists.")
            return redirect('payroll:dashboard')

        office_info = get_office_hours_and_grace()

        period = PayrollPeriod.objects.create(
            month=month,
            year=year,
            working_days=26,
            allow_overtime_compensation=allow_ot,
            office_start_time=office_info['start_time'],
            office_end_time=office_info['end_time'],
            required_daily_hours=office_info['daily_hours'],
            status='DRAFT',
            processed_by=request.user
        )

        total_gross = Decimal('0.00')
        total_ded = Decimal('0.00')
        total_net = Decimal('0.00')
        total_leave_ded = Decimal('0.00')
        total_shortfall_ded = Decimal('0.00')
        total_condoned = Decimal('0.00')
        actual_working_days = 26

        active_employees = EmployeeProfile.objects.filter(status='ACTIVE').select_related(
            'salary_structure', 'user', 'department', 'designation', 'site'
        )
        count = 0

        for emp in active_employees:
            if not hasattr(emp, 'salary_structure') or not emp.salary_structure:
                continue

            calc = compute_employee_salary(
                employee=emp,
                year=year,
                month=month,
                allow_overtime_compensation=allow_ot
            )

            actual_working_days = calc['working_days_count']
            struct = emp.salary_structure

            # Create detailed Payslip with all Master Formula breakdown fields
            ps = Payslip.objects.create(
                payroll_period=period,
                employee=emp,
                month=month,
                year=year,
                # Days
                total_working_days=Decimal(str(calc['working_days_count'])),
                present_days=Decimal(str(calc['present_days_count'])),
                paid_leaves=Decimal(str(calc['approved_sl_taken'] + calc['approved_cl_taken'])),
                loss_of_pay_days=Decimal(str(calc['total_deductible_leave_days'])),
                payable_days=Decimal(str(calc['payable_days'])),
                # Earnings
                basic_salary=calc['monthly_base_salary'],
                hra=struct.hra,
                conveyance_allowance=struct.conveyance_allowance,
                medical_allowance=struct.medical_allowance,
                special_allowance=struct.special_allowance,
                gross_earnings=calc['gross_earnings'],
                # Base Rates
                per_day_rate=calc['per_day_rate'],
                required_daily_hours=calc['required_daily_hours'],
                per_minute_rate=calc['per_minute_rate'],
                # Calendar
                calendar_days_in_month=calc['calendar_days_in_month'],
                public_holidays_count=calc['public_holidays_count'],
                weekly_offs_count=calc['weekly_offs_count'],
                working_days_count=calc['working_days_count'],
                # Part A
                approved_sl_taken=calc['approved_sl_taken'],
                sl_limit=calc['sl_limit'],
                excess_sl=calc['excess_sl'],
                approved_cl_taken=calc['approved_cl_taken'],
                cl_limit=calc['cl_limit'],
                excess_cl=calc['excess_cl'],
                unexcused_absences=calc['unexcused_absences'],
                leave_deduction=calc['leave_deduction'],
                # Part B
                total_late_minutes=calc['total_late_minutes'],
                total_overtime_minutes=calc['total_overtime_minutes'],
                net_shortfall_minutes=calc['net_shortfall_minutes'],
                shortfall_deduction=calc['shortfall_deduction'],
                allow_overtime_compensation=calc['allow_overtime_compensation'],
                # Part C
                gross_deduction=calc['gross_deduction'],
                hr_condoned_amount=calc['hr_condoned_amount'],
                final_deduction=calc['final_deduction'],
                # Standard Statutory Deductions
                provident_fund=struct.provident_fund,
                professional_tax=struct.professional_tax,
                tds=struct.tds,
                total_deductions=calc['final_deduction'] + calc['statutory_deductions'],
                net_payable=calc['net_payable'],
                status='GENERATED',
                daily_breakdown_json=calc['daily_breakdown']
            )

            total_gross += calc['gross_earnings']
            total_ded += ps.total_deductions
            total_net += calc['net_payable']
            total_leave_ded += calc['leave_deduction']
            total_shortfall_ded += calc['shortfall_deduction']
            total_condoned += calc['hr_condoned_amount']
            count += 1

        period.working_days = actual_working_days
        period.total_gross = total_gross
        period.total_deductions = total_ded
        period.total_net = total_net
        period.total_leave_deductions = total_leave_ded
        period.total_shortfall_deductions = total_shortfall_ded
        period.total_condoned_amount = total_condoned
        period.status = 'SUBMITTED'  # Awaiting Head sign-off
        period.save()

        # Notify Head of Company
        head_user = CustomUser.objects.filter(role=CustomUser.Role.HEAD).first()
        if head_user:
            create_notification(
                recipient=head_user,
                title='Payroll Awaiting Sign-off',
                message=f"Payroll for {calendar.month_name[month]} {year} (Total Net: ₹{total_net:,.2f}) computed using Master Formula and submitted for approval.",
                notification_type='PAYROLL',
                target_url='/payroll/'
            )

        log_audit_trail('PAYROLL', 'Payroll Processing', f"Payroll generated for {calendar.month_name[month]} {year} for {count} employees using Unified Master Formula.", user=request.user)
        messages.success(request, f"Payroll for {calendar.month_name[month]} {year} successfully computed using Unified Master Formula and submitted to Head for approval!")
        return redirect('payroll:period_detail', period_id=period.id)

    office_info = get_office_hours_and_grace()
    holidays_count = Holiday.objects.filter(date__year=today.year, date__month=today.month).count()

    return render(request, 'payroll/generate_payroll.html', {
        'months': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'current_month': today.month,
        'current_year': today.year,
        'office_info': office_info,
        'holidays_count': holidays_count,
    })


@login_required
def payslip_detail(request, payslip_id):
    """
    Detailed Digital Interactive Payslip View:
    Displays complete transparency of the Unified Master Formula:
    - Base Rates: Per-Day Rate (Base/30), Required Hours, Per-Minute Rate
    - Part A: Leave & Absence Deduction (Excluded Holidays & Sundays, Excess SL/CL, Unexcused)
    - Part B: Late & Overtime Shortfall Deduction (Minute-based, OT compensation)
    - Part C: Gross Deduction & HR Condonation -> Final Net Salary
    - Detailed Day-by-Day Calendar & Attendance Shortfall Ledger
    """
    payslip = get_object_or_404(
        Payslip.objects.select_related(
            'employee__user', 'employee__department', 'employee__designation',
            'employee__site', 'payroll_period', 'condoned_by'
        ),
        id=payslip_id
    )

    user = request.user
    is_owner = (payslip.employee.user == user)
    can_view = (is_owner or user.is_hr_role or user.is_head_role or user.is_superuser)

    if not can_view:
        messages.error(request, "Access Denied: You do not have permission to view this confidential salary document.")
        return redirect('portal:smart_dashboard')

    return render(request, 'payroll/payslip_detail.html', {
        'payslip': payslip,
        'period': payslip.payroll_period,
        'employee': payslip.employee,
        'daily_breakdown': payslip.daily_breakdown_json,
        'is_hr_or_head': (user.is_hr_role or user.is_head_role or user.is_superuser),
    })


@login_required
@role_required([CustomUser.Role.HR, CustomUser.Role.HEAD])
def condone_shortfall_deduction(request, payslip_id):
    """
    Action for HR/Head to waive or condone an employee's shortfall deductions.
    Recalculates:
      Final Deduction = max(0, Gross Deduction - HR Condoned Amount)
      Net Payable = max(0, Base Salary - Final Deduction)
    Supports both traditional POST redirect and AJAX requests.
    """
    payslip = get_object_or_404(Payslip.objects.select_related('payroll_period', 'employee'), id=payslip_id)

    if request.method == 'POST':
        raw_amount = request.POST.get('condoned_amount', '0').strip()
        reason = request.POST.get('condone_reason', '').strip() or request.POST.get('reason', '').strip()
        action_type = request.POST.get('action_type', 'PARTIAL')

        try:
            if action_type == 'FULL':
                condoned_amount = payslip.gross_deduction
            else:
                condoned_amount = Decimal(raw_amount)
        except Exception:
            condoned_amount = Decimal('0.00')

        condoned_amount = min(payslip.gross_deduction, max(Decimal('0.00'), condoned_amount))

        payslip.hr_condoned_amount = condoned_amount
        payslip.condone_reason = reason or "Deduction waived by HR Administration"
        payslip.condoned_by = request.user
        payslip.condoned_at = timezone.now()

        # Recalculate Final Deduction & Net Payable
        payslip.final_deduction = max(Decimal('0.00'), payslip.gross_deduction - condoned_amount)
        payslip.net_payable = max(Decimal('0.00'), payslip.basic_salary - payslip.final_deduction)
        payslip.total_deductions = payslip.final_deduction + payslip.provident_fund + payslip.professional_tax + payslip.tds
        payslip.save()

        # Update parent PayrollPeriod totals
        period = payslip.payroll_period
        all_payslips = period.payslips.all()
        period.total_net = sum(p.net_payable for p in all_payslips)
        period.total_deductions = sum(p.total_deductions for p in all_payslips)
        period.total_condoned_amount = sum(p.hr_condoned_amount for p in all_payslips)
        period.save()

        log_audit_trail('UPDATE', 'Payroll', f"HR Waived ₹{condoned_amount} deduction on payslip #{payslip.id} for {payslip.employee.emp_id}. Reason: {reason}", user=request.user)
        messages.success(request, f"Successfully waived ₹{condoned_amount:,.2f} deduction for {payslip.employee.full_name}. Net payable updated to ₹{payslip.net_payable:,.2f}.")

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'condoned_amount': str(condoned_amount),
                'final_deduction': str(payslip.final_deduction),
                'net_payable': str(payslip.net_payable),
                'message': f"Updated net salary: ₹{payslip.net_payable:,.2f}"
            })

    return redirect('payroll:period_detail', period_id=payslip.payroll_period.id)


@login_required
@head_required
def approve_payroll(request, period_id):
    """Head of Company approves and authorizes payroll disbursement."""
    period = get_object_or_404(PayrollPeriod, id=period_id)
    period.status = 'APPROVED'
    period.approved_by = request.user
    period.approved_at = timezone.now()
    period.save()

    # Update payslip statuses and notify all employees
    payslips = period.payslips.select_related('employee__user')
    payslips.update(status='APPROVED')

    for ps in payslips:
        create_notification(
            recipient=ps.employee.user,
            title=f"Payslip Available - {period.get_month_display()} {period.year}",
            message=f"Your payslip for {period.get_month_display()} {period.year} has been approved. Net payable: ₹{ps.net_payable:,.2f}",
            notification_type='PAYROLL',
            target_url='/payroll/my-payslips/'
        )

    log_audit_trail('APPROVAL', 'Payroll Management', f"Payroll period {period.get_month_display()} {period.year} approved by Head.", user=request.user)
    messages.success(request, f"Payroll for {period.get_month_display()} {period.year} has been approved and authorized for disbursement!")
    return redirect('payroll:dashboard')


@login_required
@role_required([CustomUser.Role.HR, CustomUser.Role.HEAD])
def payroll_detail(request, period_id):
    """View detailed roster of all payslips in a payroll period."""
    period = get_object_or_404(PayrollPeriod, id=period_id)
    payslips = period.payslips.select_related('employee__user', 'employee__department', 'employee__designation', 'condoned_by').all()
    return render(request, 'payroll/period_detail.html', {
        'period': period,
        'payslips': payslips,
    })


@login_required
@role_required([CustomUser.Role.HR, CustomUser.Role.HEAD])
def export_payroll_period_report(request, period_id, format_type='csv'):
    """
    Download monthly payroll report in CSV, Excel (.xlsx), or PDF format.
    Restricted to HR and Head of Company (Admin).
    """
    period = get_object_or_404(PayrollPeriod, id=period_id)
    payslips = period.payslips.select_related(
        'employee__user', 'employee__department', 'employee__designation', 'condoned_by'
    ).order_by('employee__emp_id')

    fmt = (format_type or request.GET.get('format', 'csv')).lower().strip()
    log_audit_trail('EXPORT', 'Payroll', f"Exported {period.get_month_display()} {period.year} payroll report as {fmt.upper()}", user=request.user)

    if fmt in ['excel', 'xlsx', 'xls']:
        return export_payroll_excel(period, payslips)
    elif fmt == 'pdf':
        return export_payroll_pdf(period, payslips)
    else:
        return export_payroll_csv(period, payslips)

