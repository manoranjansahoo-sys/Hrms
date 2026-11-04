from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal
import calendar
from accounts.models import CustomUser
from accounts.decorators import role_required, hr_required, head_required, log_audit_trail
from payroll.models import PayrollPeriod, Payslip, SalaryStructure
from payroll.pdf_generator import generate_payslip_pdf
from employees.models import EmployeeProfile
from attendance.models import Attendance
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
    Generates a new monthly payroll period based on actual attendance and salary structures.
    """
    today = timezone.localdate()

    if request.method == 'POST':
        month = int(request.POST.get('month', today.month))
        year = int(request.POST.get('year', today.year))
        working_days = int(request.POST.get('working_days', 26))

        # Check if already exists
        if PayrollPeriod.objects.filter(month=month, year=year).exists():
            messages.warning(request, f"Payroll for {calendar.month_name[month]} {year} already exists.")
            return redirect('payroll:dashboard')

        period = PayrollPeriod.objects.create(
            month=month,
            year=year,
            working_days=working_days,
            status='DRAFT',
            processed_by=request.user
        )

        total_gross = Decimal('0.00')
        total_ded = Decimal('0.00')
        total_net = Decimal('0.00')

        active_employees = EmployeeProfile.objects.filter(status='ACTIVE').select_related('salary_structure')
        count = 0

        for emp in active_employees:
            if not hasattr(emp, 'salary_structure') or not emp.salary_structure:
                continue

            struct = emp.salary_structure
            # Attendance in that month
            atts = Attendance.objects.filter(employee=emp, date__year=year, date__month=month)
            present_cnt = atts.filter(status='PRESENT').count()
            half_day_cnt = atts.filter(status='HALF_DAY').count()
            paid_leave_cnt = atts.filter(status='ON_LEAVE').count()

            # Loss of pay days
            lop_cnt = atts.filter(notes__icontains='Loss of Pay').count()
            payable_days = max(Decimal('0.0'), Decimal(str(working_days)) - Decimal(str(lop_cnt)))

            ratio = payable_days / Decimal(str(working_days)) if working_days > 0 else Decimal('1.0')

            # Calculated earnings
            basic = round(struct.basic_salary * ratio, 2)
            hra = round(struct.hra * ratio, 2)
            conveyance = round(struct.conveyance_allowance * ratio, 2)
            medical = round(struct.medical_allowance * ratio, 2)
            special = round(struct.special_allowance * ratio, 2)
            gross = basic + hra + conveyance + medical + special

            # Deductions
            pf = struct.provident_fund
            pt = struct.professional_tax
            tds = struct.tds
            deductions = pf + pt + tds
            net = max(Decimal('0.00'), gross - deductions)

            Payslip.objects.create(
                payroll_period=period,
                employee=emp,
                month=month,
                year=year,
                total_working_days=Decimal(str(working_days)),
                present_days=Decimal(str(present_cnt + (half_day_cnt * 0.5))),
                paid_leaves=Decimal(str(paid_leave_cnt)),
                loss_of_pay_days=Decimal(str(lop_cnt)),
                payable_days=payable_days,
                basic_salary=basic,
                hra=hra,
                conveyance_allowance=conveyance,
                medical_allowance=medical,
                special_allowance=special,
                gross_earnings=gross,
                provident_fund=pf,
                professional_tax=pt,
                tds=tds,
                total_deductions=deductions,
                net_payable=net,
                status='GENERATED'
            )

            total_gross += gross
            total_ded += deductions
            total_net += net
            count += 1

        period.total_gross = total_gross
        period.total_deductions = total_ded
        period.total_net = total_net
        period.status = 'SUBMITTED' # Submitted for Head sign-off
        period.save()

        # Notify Head of Company
        head_user = CustomUser.objects.filter(role=CustomUser.Role.HEAD).first()
        if head_user:
            create_notification(
                recipient=head_user,
                title='Payroll Awaiting Sign-off',
                message=f"Payroll for {calendar.month_name[month]} {year} (Total: ₹{total_net:,.2f}) submitted for approval.",
                notification_type='PAYROLL',
                target_url='/payroll/'
            )

        log_audit_trail('PAYROLL', 'Payroll Processing', f"Payroll generated for {calendar.month_name[month]} {year} for {count} employees.", user=request.user)
        messages.success(request, f"Payroll for {calendar.month_name[month]} {year} generated and submitted to Head for final approval!")
        return redirect('payroll:dashboard')

    return render(request, 'payroll/generate_payroll.html', {
        'months': [(i, calendar.month_name[i]) for i in range(1, 13)],
        'current_month': today.month,
        'current_year': today.year,
    })


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
    payslips = period.payslips.select_related('employee__user', 'employee__department').all()
    return render(request, 'payroll/period_detail.html', {
        'period': period,
        'payslips': payslips,
    })
