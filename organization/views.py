from decimal import Decimal
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden

from accounts.models import CustomUser
from accounts.decorators import head_required
from organization.models import Site, Holiday, OperatingSchedule, MasterDataPermission, Department
from organization.decorators import master_data_access_required
from leave_management.models import LeaveType, LeaveBalance
from attendance.models import Shift
from recruitment.models import RecruitmentJob
from employees.models import EmployeeProfile


@login_required
@master_data_access_required()
def master_data_dashboard(request):
    """
    Central Master Data Control Center for Company Configuration:
    - Official Holidays & Sunday Weekly Offs
    - Company Operating Hours (day-by-day & all-days batch)
    - Company Office Locations (Add, Edit, Delete, Position Mappings)
    - Leave Policies (Sick Leave & Paid Leave annual/monthly quotas & sync)
    - Admin-to-HR Access Delegation & Sectional Permissions
    """
    active_tab = request.GET.get('tab', 'holidays')
    current_year = timezone.localdate().year
    selected_year = int(request.GET.get('year', current_year or 2026))

    # 1. Holidays Data
    holidays = Holiday.objects.filter(date__year=selected_year).order_by('date')
    holidays_count = holidays.count()

    # 2. Operating Timings Data
    schedules = OperatingSchedule.get_weekly_schedule()
    default_shift = Shift.objects.filter(is_default=True).first()

    # 3. Locations Data
    sites = Site.objects.all().order_by('-is_active', 'name')
    locations_data = []
    for s in sites:
        pos_list = RecruitmentJob.objects.filter(
            Q(site=s) | Q(location__icontains=s.name) | Q(location__icontains=s.city)
        ).distinct()
        locations_data.append({
            'site': s,
            'positions': pos_list,
            'positions_count': pos_list.count(),
            'employees_count': s.employee_count,
        })
    eligible_managers = CustomUser.objects.filter(is_active=True).order_by('first_name', 'username')

    # 3B. Departments Data
    departments_qs = Department.objects.annotate(
        emp_count=Count('employees', filter=Q(employees__status='ACTIVE')),
        job_count=Count('recruitment_jobs')
    ).order_by('name')

    # 4. Leave Policy Data
    leave_types = LeaveType.objects.all().order_by('name')
    leave_data = []
    for lt in leave_types:
        monthly_equiv = round(float(lt.days_per_year) / 12.0, 2)
        active_balances_count = LeaveBalance.objects.filter(leave_type=lt, year=selected_year).count()
        leave_data.append({
            'leave_type': lt,
            'monthly_equiv': monthly_equiv,
            'active_balances_count': active_balances_count,
        })
    active_employees_count = EmployeeProfile.objects.filter(status='ACTIVE').count()

    # 5. Access Control & Delegation Data (Admin / Head Only)
    is_admin = (request.user.role == CustomUser.Role.HEAD or request.user.is_superuser)
    permission_settings = MasterDataPermission.get_settings()
    hr_users = CustomUser.objects.filter(role=CustomUser.Role.HR, is_active=True).order_by('first_name', 'username')
    all_eligible_users = CustomUser.objects.filter(is_active=True).exclude(role=CustomUser.Role.HEAD).order_by('first_name', 'username')

    context = {
        'active_tab': active_tab,
        'selected_year': selected_year,
        'available_years': [2025, 2026, 2027],
        'holidays': holidays,
        'holidays_count': holidays_count,
        'schedules': schedules,
        'default_shift': default_shift,
        'locations_data': locations_data,
        'departments_data': departments_qs,
        'departments_count': departments_qs.count(),
        'eligible_managers': eligible_managers,
        'leave_data': leave_data,
        'active_employees_count': active_employees_count,
        'is_admin': is_admin,
        'permission_settings': permission_settings,
        'hr_users': hr_users,
        'all_eligible_users': all_eligible_users,
        'today': timezone.localdate(),
    }
    return render(request, 'organization/master_data.html', context)


# =========================================================================
# HOLIDAY MANAGEMENT
# =========================================================================

@login_required
@master_data_access_required(section='holidays')
def holiday_create(request):
    """Add a new company declared holiday."""
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        date_str = request.POST.get('date', '').strip()
        holiday_type = request.POST.get('holiday_type', 'PUBLIC')
        description = request.POST.get('description', '').strip()
        is_optional = request.POST.get('is_optional') == 'on'

        if not title or not date_str:
            messages.error(request, "Holiday title and date are required.")
            return redirect(f"{request.META.get('HTTP_REFERER', '/master-data/')}?tab=holidays")

        try:
            h_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect(f"{request.META.get('HTTP_REFERER', '/master-data/')}?tab=holidays")

        if Holiday.objects.filter(date=h_date).exists():
            messages.warning(request, f"A holiday on {h_date.strftime('%d %b %Y')} already exists in the system.")
            return redirect(f"/master-data/?tab=holidays&year={h_date.year}")

        Holiday.objects.create(
            title=title,
            date=h_date,
            holiday_type=holiday_type,
            description=description,
            is_optional=is_optional,
        )
        messages.success(request, f"Holiday '{title}' for {h_date.strftime('%d %b %Y')} successfully recorded!")
        return redirect(f"/master-data/?tab=holidays&year={h_date.year}")

    return redirect('/master-data/?tab=holidays')


@login_required
@master_data_access_required(section='holidays')
def holiday_edit(request, holiday_id):
    """Update an existing holiday."""
    holiday = get_object_or_404(Holiday, id=holiday_id)
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        date_str = request.POST.get('date', '').strip()
        holiday_type = request.POST.get('holiday_type', 'PUBLIC')
        description = request.POST.get('description', '').strip()
        is_optional = request.POST.get('is_optional') == 'on'

        if not title or not date_str:
            messages.error(request, "Holiday title and date are required.")
            return redirect(f"/master-data/?tab=holidays&year={holiday.date.year}")

        try:
            h_date = datetime.date.fromisoformat(date_str)
        except ValueError:
            messages.error(request, "Invalid date format.")
            return redirect(f"/master-data/?tab=holidays&year={holiday.date.year}")

        # Check unique constraint if date changed
        if h_date != holiday.date and Holiday.objects.filter(date=h_date).exclude(id=holiday.id).exists():
            messages.error(request, f"Another holiday already exists on {h_date.strftime('%d %b %Y')}.")
            return redirect(f"/master-data/?tab=holidays&year={holiday.date.year}")

        holiday.title = title
        holiday.date = h_date
        holiday.holiday_type = holiday_type
        holiday.description = description
        holiday.is_optional = is_optional
        holiday.save()

        messages.success(request, f"Holiday '{holiday.title}' updated successfully.")
        return redirect(f"/master-data/?tab=holidays&year={h_date.year}")

    return redirect('/master-data/?tab=holidays')


@login_required
@master_data_access_required(section='holidays')
def holiday_delete(request, holiday_id):
    """Delete a holiday from master records."""
    holiday = get_object_or_404(Holiday, id=holiday_id)
    if request.method == 'POST':
        h_year = holiday.date.year
        title = holiday.title
        h_date_str = holiday.date.strftime('%d %b %Y')
        holiday.delete()
        messages.success(request, f"Holiday '{title}' ({h_date_str}) deleted successfully.")
        return redirect(f"/master-data/?tab=holidays&year={h_year}")

    return redirect('/master-data/?tab=holidays')


# =========================================================================
# OPERATING TIMINGS MANAGEMENT (SEPARATED DAY OR ALL DAYS)
# =========================================================================

@login_required
@master_data_access_required(section='timings')
def timing_batch_update(request):
    """
    Uniformly update Opening & Closing time for ALL working days in one click.
    Optionally sync with default shift in Attendance system.
    """
    if request.method == 'POST':
        opening_time = request.POST.get('opening_time', '').strip()
        closing_time = request.POST.get('closing_time', '').strip()
        grace_period = request.POST.get('grace_period_minutes', '15').strip()
        sync_shift = request.POST.get('sync_shift') == 'on'

        if not opening_time or not closing_time:
            messages.error(request, "Both opening time and closing time are required.")
            return redirect('/master-data/?tab=timings')

        try:
            grace_int = int(grace_period)
        except ValueError:
            grace_int = 15

        # Update all working days (Sunday remains off unless changed individually)
        updated_count = OperatingSchedule.objects.filter(is_working_day=True).update(
            opening_time=opening_time,
            closing_time=closing_time,
            grace_period_minutes=grace_int
        )

        # Synchronize default Shift if requested
        if sync_shift:
            default_shift = Shift.objects.filter(is_default=True).first()
            if default_shift:
                default_shift.start_time = opening_time
                default_shift.end_time = closing_time
                default_shift.grace_period_minutes = grace_int
                default_shift.save()

        messages.success(request, f"Updated company business hours ({opening_time} to {closing_time}) across all {updated_count} working days!")
        return redirect('/master-data/?tab=timings')

    return redirect('/master-data/?tab=timings')


@login_required
@master_data_access_required(section='timings')
def timing_day_update(request, schedule_id):
    """Update operating hours or working/off status for a separated single day."""
    schedule = get_object_or_404(OperatingSchedule, id=schedule_id)
    if request.method == 'POST':
        is_working_day = request.POST.get('is_working_day') == 'on'
        opening_time = request.POST.get('opening_time', schedule.opening_time).strip()
        closing_time = request.POST.get('closing_time', schedule.closing_time).strip()
        grace_period = request.POST.get('grace_period_minutes', str(schedule.grace_period_minutes)).strip()
        notes = request.POST.get('notes', '').strip()

        try:
            grace_int = int(grace_period)
        except ValueError:
            grace_int = schedule.grace_period_minutes

        schedule.is_working_day = is_working_day
        if is_working_day:
            schedule.opening_time = opening_time
            schedule.closing_time = closing_time
            schedule.grace_period_minutes = grace_int
            if not notes:
                notes = 'Standard working day'
        else:
            if not notes:
                notes = f"{schedule.day_name} Company Weekly Off"

        schedule.notes = notes
        schedule.save()
        schedule.refresh_from_db()

        status_text = "Working Day" if is_working_day else "Company Weekly Off"
        op_str = schedule.opening_time.strftime('%I:%M %p') if hasattr(schedule.opening_time, 'strftime') else str(schedule.opening_time)
        cl_str = schedule.closing_time.strftime('%I:%M %p') if hasattr(schedule.closing_time, 'strftime') else str(schedule.closing_time)
        messages.success(request, f"{schedule.day_name} timing updated to: {status_text} ({op_str} - {cl_str}).")
        return redirect('/master-data/?tab=timings')

    return redirect('/master-data/?tab=timings')


# =========================================================================
# COMPANY LOCATIONS MANAGEMENT (ADD, UPDATE, DELETE)
# =========================================================================

@login_required
@master_data_access_required(section='locations')
def location_create(request):
    """Add a new company office location / branch site."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        city = request.POST.get('city', '').strip()
        code = request.POST.get('code', '').strip()
        address = request.POST.get('address', '').strip()
        contact_phone = request.POST.get('contact_phone', '').strip()
        site_manager_id = request.POST.get('site_manager')

        if not name or not city:
            messages.error(request, "Location Name and City are required.")
            return redirect('/master-data/?tab=locations')

        # Auto generate code if blank
        if not code:
            clean_city = ''.join(c for c in city if c.isalnum()).upper()[:3]
            clean_name = ''.join(c for c in name if c.isalnum()).upper()[:3]
            code = f"{clean_city}-{clean_name}"
            count = 1
            base_code = code
            while Site.objects.filter(code=code).exists():
                code = f"{base_code}{count}"
                count += 1

        if Site.objects.filter(code=code).exists():
            messages.error(request, f"Location with code '{code}' already exists. Please choose a unique code.")
            return redirect('/master-data/?tab=locations')

        manager = None
        if site_manager_id:
            manager = CustomUser.objects.filter(id=site_manager_id).first()

        lat = request.POST.get('latitude', '').strip()
        lng = request.POST.get('longitude', '').strip()
        radius = request.POST.get('geofence_radius_meters', '').strip()

        latitude = None
        longitude = None
        if lat:
            try:
                latitude = Decimal(lat)
            except Exception:
                latitude = None
        if lng:
            try:
                longitude = Decimal(lng)
            except Exception:
                longitude = None

        geofence_radius = 200
        if radius:
            try:
                geofence_radius = int(radius)
            except Exception:
                geofence_radius = 200

        site = Site.objects.create(
            name=name,
            code=code,
            city=city,
            address=address,
            contact_phone=contact_phone,
            site_manager=manager,
            latitude=latitude,
            longitude=longitude,
            geofence_radius_meters=geofence_radius,
            qr_rotation_seconds=4,
            is_active=True
        )
        messages.success(request, f"Company Location '{site.name}' ({site.city}) successfully registered!")
        return redirect('/master-data/?tab=locations')

    return redirect('/master-data/?tab=locations')


@login_required
@master_data_access_required(section='locations')
def location_edit(request, site_id):
    """Update details of an existing company location."""
    site = get_object_or_404(Site, id=site_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        city = request.POST.get('city', '').strip()
        code = request.POST.get('code', '').strip()
        address = request.POST.get('address', '').strip()
        contact_phone = request.POST.get('contact_phone', '').strip()
        site_manager_id = request.POST.get('site_manager')
        is_active = request.POST.get('is_active') == 'on'
        lat = request.POST.get('latitude', '').strip()
        lng = request.POST.get('longitude', '').strip()
        radius = request.POST.get('geofence_radius_meters', '').strip()

        if not name or not city:
            messages.error(request, "Location Name and City are required.")
            return redirect('/master-data/?tab=locations')

        if code and code != site.code and Site.objects.filter(code=code).exclude(id=site.id).exists():
            messages.error(request, f"Location code '{code}' is already assigned to another site.")
            return redirect('/master-data/?tab=locations')

        manager = None
        if site_manager_id:
            manager = CustomUser.objects.filter(id=site_manager_id).first()

        site.name = name
        site.city = city
        if code:
            site.code = code
        site.address = address
        site.contact_phone = contact_phone
        site.site_manager = manager
        site.is_active = is_active

        if lat:
            try:
                site.latitude = Decimal(lat)
            except Exception:
                pass
        else:
            site.latitude = None

        if lng:
            try:
                site.longitude = Decimal(lng)
            except Exception:
                pass
        else:
            site.longitude = None

        if radius:
            try:
                site.geofence_radius_meters = int(radius)
            except Exception:
                pass

        site.save()

        messages.success(request, f"Location '{site.name}' updated successfully.")
        return redirect('/master-data/?tab=locations')

    return redirect('/master-data/?tab=locations')


@login_required
@master_data_access_required(section='locations')
def location_delete(request, site_id):
    """
    Delete or safely deactivate a company location.
    If linked to existing employees or open job requisitions, deactivates it to protect data integrity.
    """
    site = get_object_or_404(Site, id=site_id)
    if request.method == 'POST':
        site_name = site.name
        # Check linked records
        has_employees = site.employees.exists()
        has_jobs = RecruitmentJob.objects.filter(
            Q(site=site) | Q(location__icontains=site.name) | Q(location__icontains=site.city)
        ).exists()

        if has_employees or has_jobs:
            site.is_active = False
            site.save()
            messages.warning(
                request,
                f"Location '{site_name}' has linked active employees ({site.employee_count}) or jobs. "
                "It has been safely deactivated instead of deleted to protect historical records."
            )
        else:
            site.delete()
            messages.success(request, f"Location '{site_name}' has been permanently deleted.")

        return redirect('/master-data/?tab=locations')

    return redirect('/master-data/?tab=locations')


# =========================================================================
# COMPANY DEPARTMENTS MANAGEMENT (ADD, EDIT, DELETE - ADMIN ONLY)
# =========================================================================

@login_required
@head_required
def department_create(request):
    """Add a new company department in Master Data (Admin Only)."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        description = request.POST.get('description', '').strip()
        hod_id = request.POST.get('head_of_department')

        if not name:
            messages.error(request, "Department Name is required.")
            return redirect('/master-data/?tab=departments')

        if Department.objects.filter(name__iexact=name).exists():
            messages.error(request, f"Department '{name}' already exists.")
            return redirect('/master-data/?tab=departments')

        if not code:
            words = [w for w in name.split() if w]
            base_code = ("".join(w[0] for w in words[:4]) if len(words) > 1 else name[:4]).upper()
            code = base_code
            count = 1
            while Department.objects.filter(code=code).exists():
                code = f"{base_code[:3]}{count}"
                count += 1

        if Department.objects.filter(code=code).exists():
            messages.error(request, f"Department code '{code}' already exists. Please choose a unique code.")
            return redirect('/master-data/?tab=departments')

        hod = None
        if hod_id:
            hod = CustomUser.objects.filter(id=hod_id).first()

        dept = Department.objects.create(
            name=name,
            code=code,
            description=description,
            head_of_department=hod
        )
        messages.success(request, f"Company Department '{dept.name}' ({dept.code}) successfully created!")
        return redirect('/master-data/?tab=departments')

    return redirect('/master-data/?tab=departments')


@login_required
@head_required
def department_edit(request, dept_id):
    """Update details of an existing company department (Admin Only)."""
    dept = get_object_or_404(Department, id=dept_id)
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        description = request.POST.get('description', '').strip()
        hod_id = request.POST.get('head_of_department')

        if not name:
            messages.error(request, "Department Name is required.")
            return redirect('/master-data/?tab=departments')

        if Department.objects.filter(name__iexact=name).exclude(id=dept.id).exists():
            messages.error(request, f"Another department with name '{name}' already exists.")
            return redirect('/master-data/?tab=departments')

        if code and Department.objects.filter(code=code).exclude(id=dept.id).exists():
            messages.error(request, f"Department code '{code}' is already assigned to another department.")
            return redirect('/master-data/?tab=departments')

        hod = None
        if hod_id:
            hod = CustomUser.objects.filter(id=hod_id).first()

        dept.name = name
        if code:
            dept.code = code
        dept.description = description
        dept.head_of_department = hod
        dept.save()

        messages.success(request, f"Department '{dept.name}' updated successfully.")
        return redirect('/master-data/?tab=departments')

    return redirect('/master-data/?tab=departments')


@login_required
@head_required
def department_delete(request, dept_id):
    """
    Safely delete a department if no employees or jobs are linked to it (Admin Only).
    """
    dept = get_object_or_404(Department, id=dept_id)
    if request.method == 'POST':
        dept_name = dept.name
        emp_count = dept.employees.filter(status='ACTIVE').count()
        job_count = dept.recruitment_jobs.count()

        if emp_count > 0 or job_count > 0:
            messages.warning(
                request,
                f"Cannot delete Department '{dept_name}' because it currently has {emp_count} active employees and {job_count} job positions assigned to it. Reassign them first."
            )
        else:
            dept.delete()
            messages.success(request, f"Department '{dept_name}' has been permanently deleted.")

        return redirect('/master-data/?tab=departments')

    return redirect('/master-data/?tab=departments')


# =========================================================================
# LEAVE POLICY MANAGEMENT (SICK LEAVE & PAID LEAVE QUOTAS)
# =========================================================================

@login_required
@master_data_access_required(section='leave_policy')
def leave_policy_update(request, leave_type_id):
    """
    Update Sick Leave or Paid Leave quota (monthly or annually)
    and optionally synchronize all active employee leave balances.
    """
    leave_type = get_object_or_404(LeaveType, id=leave_type_id)
    if request.method == 'POST':
        allocation_mode = request.POST.get('allocation_mode', 'annual')
        annual_days_str = request.POST.get('days_per_year', '').strip()
        monthly_rate_str = request.POST.get('monthly_rate', '').strip()
        is_paid = request.POST.get('is_paid') == 'on'
        requires_attachment = request.POST.get('requires_attachment') == 'on'
        description = request.POST.get('description', '').strip()
        sync_balances = request.POST.get('sync_balances') == 'on'
        year_to_sync = int(request.POST.get('sync_year', timezone.localdate().year or 2026))

        try:
            if allocation_mode == 'monthly':
                monthly_val = Decimal(monthly_rate_str)
                annual_val = monthly_val * Decimal('12.0')
            else:
                annual_val = Decimal(annual_days_str)
                monthly_val = round(annual_val / Decimal('12.0'), 2)
        except Exception:
            messages.error(request, "Invalid quota number entered.")
            return redirect('/master-data/?tab=leaves')

        leave_type.days_per_year = annual_val
        leave_type.is_paid = is_paid
        leave_type.requires_attachment = requires_attachment
        leave_type.description = description
        leave_type.save()

        synced_count = 0
        if sync_balances:
            for emp in EmployeeProfile.objects.filter(status='ACTIVE'):
                bal, created = LeaveBalance.objects.get_or_create(
                    employee=emp,
                    leave_type=leave_type,
                    year=year_to_sync,
                    defaults={'allocated_days': annual_val}
                )
                if not created:
                    bal.allocated_days = annual_val
                    bal.save()
                synced_count += 1

        sync_msg = f" Synchronized {synced_count} active employee balances for {year_to_sync}." if sync_balances else ""
        messages.success(
            request,
            f"Updated {leave_type.name} ({leave_type.code}) quota to {annual_val} days/year "
            f"({round(float(annual_val)/12.0, 2)} days/month).{sync_msg}"
        )
        return redirect('/master-data/?tab=leaves')

    return redirect('/master-data/?tab=leaves')


@login_required
@master_data_access_required(section='leave_policy')
def leave_type_create(request):
    """Create a new custom leave policy category."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        days_per_year_str = request.POST.get('days_per_year', '12.0').strip()
        is_paid = request.POST.get('is_paid') == 'on'
        requires_attachment = request.POST.get('requires_attachment') == 'on'
        description = request.POST.get('description', '').strip()

        if not name or not code:
            messages.error(request, "Leave Name and Code are required.")
            return redirect('/master-data/?tab=leaves')

        if LeaveType.objects.filter(code=code).exists():
            messages.error(request, f"Leave code '{code}' already exists.")
            return redirect('/master-data/?tab=leaves')

        try:
            days_val = Decimal(days_per_year_str)
        except Exception:
            days_val = Decimal('12.0')

        LeaveType.objects.create(
            name=name,
            code=code,
            days_per_year=days_val,
            is_paid=is_paid,
            requires_attachment=requires_attachment,
            description=description
        )
        messages.success(request, f"New Leave Policy '{name}' ({code}) with {days_val} days/year created successfully!")
        return redirect('/master-data/?tab=leaves')

    return redirect('/master-data/?tab=leaves')


# =========================================================================
# ACCESS DELEGATION & PERMISSIONS MANAGEMENT (ADMIN ONLY)
# =========================================================================

@login_required
@head_required
def permissions_update(request):
    """
    Admin control to delegate Master Data access to all HR Administrators
    or specific designated employees/positions.
    """
    if request.method == 'POST':
        permission = MasterDataPermission.get_settings()

        allow_all_hr = request.POST.get('allow_all_hr') == 'on'
        can_manage_holidays = request.POST.get('can_manage_holidays') == 'on'
        can_manage_timings = request.POST.get('can_manage_timings') == 'on'
        can_manage_locations = request.POST.get('can_manage_locations') == 'on'
        can_manage_leave_policy = request.POST.get('can_manage_leave_policy') == 'on'

        user_ids = request.POST.getlist('allowed_users')

        permission.allow_all_hr = allow_all_hr
        permission.can_manage_holidays = can_manage_holidays
        permission.can_manage_timings = can_manage_timings
        permission.can_manage_locations = can_manage_locations
        permission.can_manage_leave_policy = can_manage_leave_policy
        permission.save()

        # Update allowed users M2M
        permission.allowed_users.set(CustomUser.objects.filter(id__in=user_ids))

        messages.success(
            request,
            f"Master Data permissions updated! HR Access: {'ENABLED for all HR' if allow_all_hr else 'Restricted'}. "
            f"{len(user_ids)} specific staff members delegated access."
        )
        return redirect('/master-data/?tab=access')

    return redirect('/master-data/?tab=access')
