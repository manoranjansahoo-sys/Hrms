import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from accounts.models import CustomUser, AuditLog
from accounts.decorators import role_required, hr_required, log_audit_trail
from employees.models import EmployeeProfile, EmployeeDocument, ProfileCorrectionRequest
from employees.forms import EmployeeCreateForm, ProfileCorrectionForm
from organization.models import Department, Site
from leave_management.models import LeaveBalance
from payroll.models import SalaryStructure


@login_required
def employee_list(request):
    """
    Searchable, filterable list of employees with role-aware actions.
    """
    user = request.user
    profiles = EmployeeProfile.objects.select_related('user', 'department', 'designation', 'site').all()

    # If Site Manager, filter to their managed site by default unless viewing all
    if user.is_site_manager_role and not (user.is_hr_role or user.is_head_role):
        managed_sites = user.managed_sites.all()
        profiles = profiles.filter(site__in=managed_sites)

    # Filters
    search_query = request.GET.get('search', '')
    dept_id = request.GET.get('department', '')
    site_id = request.GET.get('site', '')
    status_filter = request.GET.get('status', '')

    if search_query:
        profiles = profiles.filter(
            Q(emp_id__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    if dept_id:
        profiles = profiles.filter(department_id=dept_id)
    if site_id:
        profiles = profiles.filter(site_id=site_id)
    if status_filter:
        profiles = profiles.filter(status=status_filter)

    paginator = Paginator(profiles, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    departments = Department.objects.all()
    sites = Site.objects.filter(is_active=True)

    return render(request, 'employees/employee_list.html', {
        'page_obj': page_obj,
        'departments': departments,
        'sites': sites,
        'search_query': search_query,
        'selected_dept': dept_id,
        'selected_site': site_id,
        'selected_status': status_filter,
    })


@login_required
def employee_detail(request, emp_id):
    """
    Detailed employee profile with strict RBAC:
    Confidential salary and bank details are ONLY visible to the employee themselves, HR, or Head.
    """
    emp = get_object_or_404(EmployeeProfile.objects.select_related('user', 'department', 'designation', 'site', 'reporting_manager'), emp_id=emp_id)
    user = request.user

    # Confidentiality check
    is_self = (emp.user == user)
    can_view_confidential = (is_self or user.is_hr_role or user.is_head_role or user.is_superuser)

    # Site manager permission: Can only view if belongs to their site
    if user.is_site_manager_role and not (user.is_hr_role or user.is_head_role):
        if emp.site and emp.site not in user.managed_sites.all():
            messages.error(request, "Permission Denied: Employee belongs to a different site.")
            return redirect('employees:employee_list')

    documents = emp.documents.all()
    leave_balances = LeaveBalance.objects.filter(employee=emp, year=timezone.localdate().year).select_related('leave_type')
    salary_structure = None
    if can_view_confidential and hasattr(emp, 'salary_structure'):
        salary_structure = emp.salary_structure

    return render(request, 'employees/employee_detail.html', {
        'employee': emp,
        'is_self': is_self,
        'can_view_confidential': can_view_confidential,
        'documents': documents,
        'leave_balances': leave_balances,
        'salary_structure': salary_structure,
    })


@login_required
@hr_required
def employee_create(request):
    """HR creates a new employee account with auto-generated EMP ID."""
    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST)
        if form.is_valid():
            # 1. Create CustomUser account
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            phone = form.cleaned_data.get('phone', '')
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            role = form.cleaned_data['role']
            password = form.cleaned_data['password']

            if CustomUser.objects.filter(username__iexact=username).exists():
                messages.error(request, f"Username '{username}' already exists. Please choose a different one.")
                return render(request, 'employees/employee_create.html', {'form': form})

            if CustomUser.objects.filter(email__iexact=email).exists():
                messages.error(request, f"An account with email '{email}' already exists. Please check or use another email.")
                return render(request, 'employees/employee_create.html', {'form': form})

            user_obj = CustomUser.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                role=role,
                password=password
            )
            if phone:
                user_obj.phone = phone
                user_obj.save(update_fields=['phone'])

            # 2. Auto-generate next EMP ID (e.g. EMP105)
            last_emp = EmployeeProfile.objects.order_by('-id').first()
            next_num = 101
            if last_emp and last_emp.emp_id.startswith('EMP'):
                try:
                    num_part = int(last_emp.emp_id.replace('EMP', ''))
                    next_num = max(101, num_part + 1)
                except ValueError:
                    next_num = last_emp.id + 100
            new_emp_id = f"EMP{next_num}"

            # 3. Create EmployeeProfile
            profile = form.save(commit=False)
            profile.user = user_obj
            profile.emp_id = new_emp_id
            if email:
                profile.personal_email = email
            profile.save()

            log_audit_trail('CREATE', 'Employee Management', f"New employee created: {new_emp_id} ({user_obj.get_full_name()})", user=request.user)
            messages.success(request, f"Employee {user_obj.get_full_name()} ({new_emp_id}) onboarded successfully! They can log in immediately with Username '{username}', Email '{email}', or Mobile '{phone}' and their configured password.")
            return redirect('employees:employee_detail', emp_id=new_emp_id)
    else:
        form = EmployeeCreateForm()

    return render(request, 'employees/employee_create.html', {'form': form})


@login_required
def profile_correction_request(request):
    """Employees can request corrections for their own personal or banking information."""
    emp = getattr(request.user, 'employee_profile', None)
    if not emp:
        messages.error(request, "Employee profile not found.")
        return redirect('portal:home')

    if request.method == 'POST':
        form = ProfileCorrectionForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.employee = emp
            req.save()
            log_audit_trail('CREATE', 'Profile Corrections', f"Correction requested by {emp.emp_id} for {req.field_name}", user=request.user)
            messages.success(request, "Your profile correction request has been submitted to HR for review.")
            return redirect('employees:employee_detail', emp_id=emp.emp_id)
    else:
        form = ProfileCorrectionForm()

    return render(request, 'employees/profile_correction_form.html', {'form': form, 'employee': emp})


@login_required
@hr_required
def profile_corrections_list(request):
    """HR views and processes pending profile correction requests."""
    corrections = ProfileCorrectionRequest.objects.select_related('employee__user').all()
    return render(request, 'employees/profile_corrections_list.html', {'corrections': corrections})


@login_required
@hr_required
def review_profile_correction(request, request_id):
    """HR Approves or Rejects a profile correction request."""
    req = get_object_or_404(ProfileCorrectionRequest, id=request_id)
    action = request.POST.get('action')
    notes = request.POST.get('notes', '')

    if action == 'APPROVE':
        req.status = 'APPROVED'
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.review_notes = notes
        req.save()

        # If matching a direct profile field, update it automatically
        field = req.field_name.lower().replace(' ', '_')
        if hasattr(req.employee, field):
            setattr(req.employee, field, req.proposed_value)
            req.employee.save()

        log_audit_trail('APPROVAL', 'Profile Corrections', f"Approved profile change for {req.employee.emp_id}: {req.field_name}", user=request.user)
        messages.success(request, f"Profile correction for {req.employee.emp_id} has been approved.")
    elif action == 'REJECT':
        req.status = 'REJECTED'
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.review_notes = notes
        req.save()
        log_audit_trail('APPROVAL', 'Profile Corrections', f"Rejected profile change for {req.employee.emp_id}: {req.field_name}", user=request.user)
        messages.info(request, f"Profile correction for {req.employee.emp_id} has been rejected.")

    return redirect('employees:profile_corrections_list')


@login_required
@hr_required
def export_employees_csv(request):
    """Export employee roster to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Employee_Directory_{timezone.localdate()}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Emp ID', 'Full Name', 'Email', 'Phone', 'Department', 'Designation', 'Site', 'Employment Type', 'Joining Date', 'Status'])

    for emp in EmployeeProfile.objects.select_related('user', 'department', 'designation', 'site').all():
        writer.writerow([
            emp.emp_id,
            emp.full_name,
            emp.email,
            emp.phone,
            emp.department.name if emp.department else '',
            emp.designation.title if emp.designation else '',
            emp.site.name if emp.site else '',
            emp.get_employment_type_display(),
            emp.joining_date.strftime('%Y-%m-%d') if emp.joining_date else '',
            emp.get_status_display()
        ])

    return response
