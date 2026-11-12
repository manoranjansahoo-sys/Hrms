"""
payroll/calculator.py
Unified Master Formula Engine for Monthly Employee Salary Calculation.

Formula Specifications:
-----------------------
Base Rates:
  Per-Day Rate = Monthly Base Salary / 30
  Required Daily Hours = Office End Time - Office Start Time
  Per-Minute Rate = Per-Day Rate / (Required Daily Hours * 60)

Part A — Leave & Absence Deduction (Day-Based):
  Exclude Public Holidays and Weekly Offs (Sundays) from working days.
  Excess SL = max(0, Approved SL Taken - SL Limit)
  Excess CL = max(0, Approved CL Taken - CL Limit)
  Unexcused Absences = Working days with no check-in and no approved leave
  Leave Deduction = (Excess SL + Excess CL + Unexcused Absences) * Per-Day Rate

Part B — Late & Overtime Shortfall Deduction (Minute-Based):
  For every present working day:
    Late Minutes = max(0, Check-In - Shift Start) (if beyond grace period)
    Overtime Minutes = max(0, Check-Out - Shift End)
    If Master Data allows Overtime Compensation:
        Net Shortfall Minutes = max(0, Late Minutes - Overtime Minutes)
    Otherwise (strict mode):
        Net Shortfall Minutes = Late Minutes
    Daily Shortfall Deduction = Net Shortfall Minutes * Per-Minute Rate
  (HR can waive/condone individual days or let system auto-waive when OT covers late arrival).

Part C — Final Monthly Net Salary & HR Condone:
  Gross Deduction = Leave Deduction + sum(Daily Shortfall Deductions)
  Final Deduction = max(0, Gross Deduction - HR Condoned Amount)
  Net Payable Salary = max(0, Monthly Base Salary - Final Deduction)
"""

import calendar
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP
from django.utils import timezone
from organization.models import Holiday, OperatingSchedule
from leave_management.models import LeaveType, LeaveRequest
from attendance.models import Attendance, Shift


def round_decimal(val, places=2):
    """Safely rounds decimal numbers using ROUND_HALF_UP."""
    if val is None:
        return Decimal('0.00')
    if not isinstance(val, Decimal):
        val = Decimal(str(val))
    q = Decimal('10') ** -places
    return val.quantize(q, rounding=ROUND_HALF_UP)


def get_office_hours_and_grace(employee=None, target_date=None):
    """
    Retrieves the corporate start time, end time, daily hours, and grace period
    from Shift or OperatingSchedule.
    """
    shift = None
    if employee:
        # Check if employee has assigned shift via attendance or default
        shift = Shift.objects.filter(is_default=True).first() or Shift.objects.first()

    schedule = None
    day_idx = target_date.weekday() if target_date else 0
    schedules = {s.day_of_week: s for s in OperatingSchedule.get_weekly_schedule()}
    schedule = schedules.get(day_idx)

    start_t = time(9, 30)
    end_t = time(18, 30)
    grace_mins = 15

    if shift and shift.start_time and shift.end_time:
        start_t = shift.start_time
        end_t = shift.end_time
        grace_mins = shift.grace_period_minutes
    elif schedule and schedule.opening_time and schedule.closing_time:
        start_t = schedule.opening_time
        end_t = schedule.closing_time
        grace_mins = schedule.grace_period_minutes

    # Calculate required daily hours
    start_total_mins = start_t.hour * 60 + start_t.minute
    end_total_mins = end_t.hour * 60 + end_t.minute
    diff_mins = max(60, end_total_mins - start_total_mins)
    daily_hours = Decimal(str(round(diff_mins / 60.0, 2)))

    return {
        'start_time': start_t,
        'end_time': end_t,
        'grace_minutes': grace_mins,
        'daily_hours': daily_hours,
        'daily_minutes': diff_mins
    }


def compute_employee_salary(
    employee,
    year,
    month,
    allow_overtime_compensation=True,
    custom_hr_condoned=None,
    condone_reason='',
    condoned_by=None
):
    """
    Computes complete monthly payroll for a single employee using the
    Unified Master Formula. Returns a structured dictionary with all components.
    """
    # -------------------------------------------------------------
    # 1. Base Rates
    # -------------------------------------------------------------
    salary_struct = getattr(employee, 'salary_structure', None)
    base_salary = salary_struct.basic_salary if salary_struct else Decimal('0.00')

    # Base Rates:
    # Per-Day Rate = Monthly Base Salary / 30
    per_day_rate = round_decimal(base_salary / Decimal('30.0'), 2)

    # Required Daily Hours & Per-Minute Rate
    office_info = get_office_hours_and_grace(employee=employee, target_date=date(year, month, 1))
    daily_hours = office_info['daily_hours']
    daily_minutes = office_info['daily_minutes']

    # Per-Minute Rate = Per-Day Rate / (Required Daily Hours * 60)
    if daily_minutes > 0:
        per_minute_rate = round_decimal(per_day_rate / Decimal(str(daily_minutes)), 4)
    else:
        per_minute_rate = Decimal('0.0000')

    # -------------------------------------------------------------
    # 2. Calendar Days, Public Holidays & Weekly Offs (Sundays)
    # -------------------------------------------------------------
    _, total_calendar_days = calendar.monthrange(year, month)
    holidays_qs = Holiday.objects.filter(date__year=year, date__month=month)
    holiday_dates = {h.date: h.title for h in holidays_qs}

    weekly_schedules = {s.day_of_week: s for s in OperatingSchedule.get_weekly_schedule()}

    working_dates = []
    public_holiday_dates = []
    weekly_off_dates = []

    for d in range(1, total_calendar_days + 1):
        cur_date = date(year, month, d)
        if cur_date in holiday_dates:
            public_holiday_dates.append(cur_date)
        elif cur_date.weekday() == 6 or (cur_date.weekday() in weekly_schedules and not weekly_schedules[cur_date.weekday()].is_working_day):
            weekly_off_dates.append(cur_date)
        else:
            working_dates.append(cur_date)

    working_days_count = len(working_dates)
    public_holidays_count = len(public_holiday_dates)
    weekly_offs_count = len(weekly_off_dates)

    # -------------------------------------------------------------
    # 3. Part A — Leave & Absence Deduction (Day-Based)
    # -------------------------------------------------------------
    # Monthly Quotas / Limits from LeaveType
    sl_type = LeaveType.objects.filter(code='SL').first()
    cl_type = LeaveType.objects.filter(code__in=['CL', 'PL']).first()

    # SL Limit (e.g. 10/12 = ~1.0/month)
    sl_limit = round_decimal((sl_type.days_per_year / Decimal('12.0')) if sl_type else Decimal('1.0'), 1)
    # CL Limit (e.g. 18/12 = 1.5/month)
    cl_limit = round_decimal((cl_type.days_per_year / Decimal('12.0')) if cl_type else Decimal('1.0'), 1)

    # Approved Leaves for this employee in this month
    approved_leaves = LeaveRequest.objects.filter(
        employee=employee,
        status=LeaveRequest.Status.APPROVED,
        start_date__lte=date(year, month, total_calendar_days),
        end_date__gte=date(year, month, 1)
    ).select_related('leave_type')

    approved_leave_map = {}  # date -> leave_type code
    approved_sl_days = Decimal('0.0')
    approved_cl_days = Decimal('0.0')

    for req in approved_leaves:
        cur = max(req.start_date, date(year, month, 1))
        last = min(req.end_date, date(year, month, total_calendar_days))
        while cur <= last:
            # Leave applies only on working days (not on holidays or weekly offs)
            if cur in working_dates:
                val = Decimal('0.5') if req.is_half_day else Decimal('1.0')
                code = req.leave_type.code.upper()
                approved_leave_map[cur] = code
                if code == 'SL':
                    approved_sl_days += val
                else:
                    approved_cl_days += val
            cur += timedelta(days=1)

    # Excess SL & CL
    excess_sl = max(Decimal('0.0'), approved_sl_days - sl_limit)
    excess_cl = max(Decimal('0.0'), approved_cl_days - cl_limit)

    # Unexcused Absences: Working days with no check-in and no approved leave
    attendances_qs = Attendance.objects.filter(
        employee=employee,
        date__year=year,
        date__month=month
    ).select_related('shift')
    attendance_map = {att.date: att for att in attendances_qs}

    unexcused_absences = Decimal('0.0')
    present_days_count = Decimal('0.0')

    daily_breakdown = []

    # -------------------------------------------------------------
    # 4. Part B — Late & Overtime Shortfall Deduction (Minute-Based)
    # -------------------------------------------------------------
    total_late_minutes = 0
    total_overtime_minutes = 0
    net_shortfall_minutes = 0
    total_shortfall_deduction = Decimal('0.00')

    for cur_date in range(1, total_calendar_days + 1):
        dt = date(year, month, cur_date)
        day_name = dt.strftime('%A')

        if dt in holiday_dates:
            daily_breakdown.append({
                'date': str(dt),
                'day': day_name,
                'status': 'PUBLIC_HOLIDAY',
                'status_label': f"Public Holiday: {holiday_dates[dt]}",
                'is_working_day': False,
                'punch_in': None,
                'punch_out': None,
                'late_minutes': 0,
                'overtime_minutes': 0,
                'net_shortfall_minutes': 0,
                'shortfall_deduction': '0.00',
                'waived': True,
                'notes': holiday_dates[dt]
            })
            continue

        if dt in weekly_off_dates:
            daily_breakdown.append({
                'date': str(dt),
                'day': day_name,
                'status': 'WEEKLY_OFF',
                'status_label': 'Sunday Company Weekly Off',
                'is_working_day': False,
                'punch_in': None,
                'punch_out': None,
                'late_minutes': 0,
                'overtime_minutes': 0,
                'net_shortfall_minutes': 0,
                'shortfall_deduction': '0.00',
                'waived': True,
                'notes': 'Weekly Off'
            })
            continue

        # WORKING DAY
        att = attendance_map.get(dt)
        day_office = get_office_hours_and_grace(employee=employee, target_date=dt)
        shift_start = day_office['start_time']
        shift_end = day_office['end_time']
        grace = day_office['grace_minutes']

        # Scenario A: Approved Leave
        if dt in approved_leave_map:
            l_code = approved_leave_map[dt]
            daily_breakdown.append({
                'date': str(dt),
                'day': day_name,
                'status': 'APPROVED_LEAVE',
                'status_label': f"Approved Leave ({l_code})",
                'is_working_day': True,
                'punch_in': None,
                'punch_out': None,
                'late_minutes': 0,
                'overtime_minutes': 0,
                'net_shortfall_minutes': 0,
                'shortfall_deduction': '0.00',
                'waived': False,
                'notes': f"Approved {l_code}"
            })
            continue

        # Scenario B: No check-in / absent on a working day with NO approved leave
        if not att or not att.punch_in or att.status == 'ABSENT':
            unexcused_absences += Decimal('1.0')
            daily_breakdown.append({
                'date': str(dt),
                'day': day_name,
                'status': 'UNEXCUSED_ABSENCE',
                'status_label': 'Unexcused Absence (No Punch-in)',
                'is_working_day': True,
                'punch_in': None,
                'punch_out': None,
                'late_minutes': 0,
                'overtime_minutes': 0,
                'net_shortfall_minutes': 0,
                'shortfall_deduction': '0.00',
                'waived': False,
                'notes': 'No check-in & no leave applied'
            })
            continue

        # Scenario C: Present on Working Day -> Calculate Minute-Based Shortfall
        present_days_count += Decimal('1.0')
        pin_local = timezone.localtime(att.punch_in).time() if timezone.is_aware(att.punch_in) else att.punch_in.time()
        pout_local = None
        if att.punch_out:
            pout_local = timezone.localtime(att.punch_out).time() if timezone.is_aware(att.punch_out) else att.punch_out.time()

        # Check Late Arrival (beyond grace period)
        pin_total_mins = pin_local.hour * 60 + pin_local.minute
        start_total_mins = shift_start.hour * 60 + shift_start.minute
        late_mins = 0
        if pin_total_mins > (start_total_mins + grace):
            late_mins = pin_total_mins - start_total_mins

        # Check Overtime (beyond shift end)
        ot_mins = 0
        if pout_local:
            pout_total_mins = pout_local.hour * 60 + pout_local.minute
            end_total_mins = shift_end.hour * 60 + shift_end.minute
            if pout_total_mins > end_total_mins:
                ot_mins = pout_total_mins - end_total_mins

        # Net Shortfall Minutes
        if allow_overtime_compensation:
            net_shortfall = max(0, late_mins - ot_mins)
            is_auto_waived = (late_mins > 0 and ot_mins >= late_mins)
        else:
            net_shortfall = late_mins
            is_auto_waived = False

        daily_shortfall_amt = round_decimal(Decimal(str(net_shortfall)) * per_minute_rate, 2)

        total_late_minutes += late_mins
        total_overtime_minutes += ot_mins
        net_shortfall_minutes += net_shortfall
        total_shortfall_deduction += daily_shortfall_amt

        daily_breakdown.append({
            'date': str(dt),
            'day': day_name,
            'status': 'PRESENT',
            'status_label': 'Present' if (late_mins == 0) else ('Late (Covered by OT)' if is_auto_waived else 'Late Arrival'),
            'is_working_day': True,
            'punch_in': pin_local.strftime('%I:%M %p'),
            'punch_out': pout_local.strftime('%I:%M %p') if pout_local else 'Missing Punch-out',
            'late_minutes': late_mins,
            'overtime_minutes': ot_mins,
            'net_shortfall_minutes': net_shortfall,
            'shortfall_deduction': str(daily_shortfall_amt),
            'waived': is_auto_waived,
            'notes': f"Late: {late_mins}m, OT: {ot_mins}m" if (late_mins or ot_mins) else "On Time"
        })

    # Part A Leave Deduction:
    # Leave Deduction = (Excess SL + Excess CL + Unexcused Absences) * Per-Day Rate
    total_deductible_leave_days = excess_sl + excess_cl + unexcused_absences
    leave_deduction = round_decimal(total_deductible_leave_days * per_day_rate, 2)

    # -------------------------------------------------------------
    # 5. Part C — Final Monthly Net Salary & HR Condone
    # -------------------------------------------------------------
    # Gross Deduction = Leave Deduction + sum(Daily Shortfall Deductions)
    gross_deduction = round_decimal(leave_deduction + total_shortfall_deduction, 2)

    # HR Condoned Amount
    hr_condoned = Decimal('0.00')
    if custom_hr_condoned is not None:
        hr_condoned = round_decimal(custom_hr_condoned, 2)

    # Final Deduction = max(0, Gross Deduction - HR Condoned Amount)
    final_deduction = max(Decimal('0.00'), gross_deduction - hr_condoned)

    # Net Payable Salary = max(0, Monthly Base Salary - Final Deduction)
    # (Including allowances if configured in SalaryStructure)
    allowances_total = Decimal('0.00')
    statutory_deductions = Decimal('0.00')
    if salary_struct:
        allowances_total = (
            salary_struct.hra +
            salary_struct.conveyance_allowance +
            salary_struct.medical_allowance +
            salary_struct.special_allowance
        )
        statutory_deductions = (
            salary_struct.provident_fund +
            salary_struct.professional_tax +
            salary_struct.tds
        )

    gross_earnings = round_decimal(base_salary + allowances_total, 2)
    net_payable = max(Decimal('0.00'), base_salary - final_deduction)

    payable_days = max(Decimal('0.0'), Decimal(str(working_days_count)) - total_deductible_leave_days)

    return {
        'employee': employee,
        'year': year,
        'month': month,
        # Base Rates
        'monthly_base_salary': base_salary,
        'per_day_rate': per_day_rate,
        'required_daily_hours': daily_hours,
        'per_minute_rate': per_minute_rate,
        # Calendar
        'calendar_days_in_month': total_calendar_days,
        'public_holidays_count': public_holidays_count,
        'weekly_offs_count': weekly_offs_count,
        'working_days_count': working_days_count,
        'present_days_count': present_days_count,
        'payable_days': payable_days,
        # Part A
        'approved_sl_taken': approved_sl_days,
        'sl_limit': sl_limit,
        'excess_sl': excess_sl,
        'approved_cl_taken': approved_cl_days,
        'cl_limit': cl_limit,
        'excess_cl': excess_cl,
        'unexcused_absences': unexcused_absences,
        'total_deductible_leave_days': total_deductible_leave_days,
        'leave_deduction': leave_deduction,
        # Part B
        'total_late_minutes': total_late_minutes,
        'total_overtime_minutes': total_overtime_minutes,
        'net_shortfall_minutes': net_shortfall_minutes,
        'shortfall_deduction': total_shortfall_deduction,
        'allow_overtime_compensation': allow_overtime_compensation,
        # Part C
        'gross_deduction': gross_deduction,
        'hr_condoned_amount': hr_condoned,
        'final_deduction': final_deduction,
        'condone_reason': condone_reason,
        'condoned_by': condoned_by,
        'condoned_at': timezone.now() if hr_condoned > 0 else None,
        # Earnings & Payout
        'allowances_total': allowances_total,
        'gross_earnings': gross_earnings,
        'statutory_deductions': statutory_deductions,
        'net_payable': net_payable,
        # Ledger
        'daily_breakdown': daily_breakdown
    }

