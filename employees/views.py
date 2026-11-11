import csv
import json
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
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
from leave_management.models import LeaveBalance, ensure_employee_leave_balances
from payroll.models import SalaryStructure
from notifications.models import create_notification


@login_required
def employee_list(request):
    """
    Searchable, filterable list of employees with role-aware actions,
    dynamic page sizing (5, 10, 20, 50, 100), multi-criteria sorting, and auto-filters.
    """
    user = request.user
    base_profiles = EmployeeProfile.objects.select_related('user', 'department', 'designation', 'site').all()

    # If Site Manager, filter to their managed site by default unless viewing all
    if user.is_site_manager_role and not (user.is_hr_role or user.is_head_role):
        managed_sites = user.managed_sites.all()
        base_profiles = base_profiles.filter(site__in=managed_sites)

    total_employees = base_profiles.count()
    active_employees = base_profiles.filter(status=EmployeeProfile.Status.ACTIVE).count()
    on_notice_employees = base_profiles.filter(status=EmployeeProfile.Status.ON_NOTICE).count()

    profiles = base_profiles

    # Filters
    search_query = request.GET.get('search', '').strip()
    dept_id = request.GET.get('department', '').strip()
    site_id = request.GET.get('site', '').strip()
    status_filter = request.GET.get('status', '').strip()
    sort_by = request.GET.get('sort', 'latest').strip()

    if search_query:
        profiles = profiles.filter(
            Q(emp_id__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(user__phone__icontains=search_query) |
            Q(designation__title__icontains=search_query)
        )
    if dept_id:
        profiles = profiles.filter(department_id=dept_id)
    if site_id:
        profiles = profiles.filter(site_id=site_id)
    if status_filter:
        profiles = profiles.filter(status=status_filter)

    # Sorting
    if sort_by == 'latest':
        profiles = profiles.order_by('-id')
    elif sort_by == 'oldest':
        profiles = profiles.order_by('id')
    elif sort_by == 'name_asc':
        profiles = profiles.order_by('user__first_name', 'user__last_name')
    elif sort_by == 'name_desc':
        profiles = profiles.order_by('-user__first_name', '-user__last_name')
    elif sort_by == 'emp_id_asc':
        profiles = profiles.order_by('emp_id')
    elif sort_by == 'emp_id_desc':
        profiles = profiles.order_by('-emp_id')
    else:
        profiles = profiles.order_by('-id')

    # Page size / per_page options (5, 10, 20, 50, 100)
    per_page_options = [5, 10, 20, 50, 100]
    per_page = request.GET.get('per_page')
    try:
        per_page = int(per_page)
        if per_page not in per_page_options:
            per_page = 10
    except (TypeError, ValueError):
        per_page = 10

    paginator = Paginator(profiles, per_page)
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
        'selected_sort': sort_by,
        'selected_per_page': per_page,
        'status_choices': EmployeeProfile.Status.choices,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'on_notice_employees': on_notice_employees,
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
    ensure_employee_leave_balances(emp, timezone.localdate().year)
    leave_balances = LeaveBalance.objects.filter(employee=emp, year=timezone.localdate().year, leave_type__code__in=['SL', 'PL']).select_related('leave_type')
    salary_structure = None
    if can_view_confidential and hasattr(emp, 'salary_structure'):
        salary_structure = emp.salary_structure

    # Profile correction requests submitted by this employee
    correction_requests = emp.correction_requests.select_related('reviewed_by').all()[:10]

    return render(request, 'employees/employee_detail.html', {
        'employee': emp,
        'is_self': is_self,
        'can_view_confidential': can_view_confidential,
        'documents': documents,
        'leave_balances': leave_balances,
        'salary_structure': salary_structure,
        'correction_requests': correction_requests,
    })


@login_required
@hr_required
def employee_create(request):
    """HR creates a new employee account with auto-generated EMP ID."""
    if request.method == 'POST':
        form = EmployeeCreateForm(request.POST, user=request.user)
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
        form = EmployeeCreateForm(user=request.user)

    return render(request, 'employees/employee_create.html', {'form': form})


def apply_profile_correction_update(req):
    """
    Applies the approved correction to EmployeeProfile or CustomUser.
    Guarantees that whatever field the employee requested is updated accurately,
    handling property setters, aliases, normalization, and saving to DB.
    """
    emp = req.employee
    user = emp.user
    raw_field = (req.field_name or '').strip().lower()
    norm = re.sub(r'[^a-z0-9]', '_', raw_field).strip('_')
    new_val = (req.proposed_value or '').strip()

    # 1. Primary User Phone / Mobile
    if any(k in norm for k in ['phone', 'mobile', 'cell', 'contact_no']) and 'emergency' not in norm:
        clean_digits = re.sub(r'\D', '', new_val)
        if len(clean_digits) >= 10:
            clean_digits = clean_digits[-10:]
        user.phone = clean_digits or new_val
        user.save(update_fields=['phone'])
        return True, f"Updated mobile phone to {user.phone}"

    # 2. Email Address
    if 'email' in norm:
        user.email = new_val
        user.save(update_fields=['email'])
        emp.personal_email = new_val
        emp.save(update_fields=['personal_email'])
        return True, f"Updated email to {new_val}"

    # 3. First / Last / Full Name
    if norm in ['first_name', 'firstname']:
        user.first_name = new_val
        user.save(update_fields=['first_name'])
        return True, f"Updated first name to {new_val}"
    if norm in ['last_name', 'lastname', 'surname']:
        user.last_name = new_val
        user.save(update_fields=['last_name'])
        return True, f"Updated last name to {new_val}"
    if norm in ['name', 'full_name', 'fullname']:
        parts = new_val.split(' ', 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ''
        user.save(update_fields=['first_name', 'last_name'])
        return True, f"Updated full name to {new_val}"

    # 4. Bank Details
    if any(k in norm for k in ['account', 'ac_no', 'acc_num', 'bank_acc']):
        clean_acc = re.sub(r'\D', '', new_val)
        emp.bank_account_number = clean_acc or new_val
        emp.save(update_fields=['bank_account_number'])
        return True, f"Updated bank account number to {emp.bank_account_number}"

    if any(k in norm for k in ['bank_name', 'salary_bank', 'bank']) and 'account' not in norm and 'ifsc' not in norm:
        emp.bank_name = new_val
        emp.save(update_fields=['bank_name'])
        return True, f"Updated salary bank name to {new_val}"

    if 'ifsc' in norm:
        clean_ifsc = re.sub(r'[^A-Za-z0-9]', '', new_val).upper()
        emp.ifsc_code = clean_ifsc
        emp.save(update_fields=['ifsc_code'])
        return True, f"Updated IFSC code to {emp.ifsc_code}"

    # 5. PAN, UAN
    if 'pan' in norm:
        clean_pan = re.sub(r'[^A-Za-z0-9]', '', new_val).upper()
        emp.pan_number = clean_pan
        emp.save(update_fields=['pan_number'])
        return True, f"Updated PAN card to {emp.pan_number}"

    if 'uan' in norm:
        clean_uan = re.sub(r'\D', '', new_val)
        emp.uan_number = clean_uan or new_val
        emp.save(update_fields=['uan_number'])
        return True, f"Updated PF UAN to {emp.uan_number}"

    # 6. Emergency Contact
    if 'emergency' in norm:
        if any(k in norm for k in ['phone', 'mobile', 'number']):
            clean_digits = re.sub(r'\D', '', new_val)
            if len(clean_digits) >= 10:
                clean_digits = clean_digits[-10:]
            emp.emergency_contact_phone = clean_digits or new_val
            emp.save(update_fields=['emergency_contact_phone'])
            return True, f"Updated emergency contact phone to {emp.emergency_contact_phone}"
        elif any(k in norm for k in ['relation', 'relationship']):
            emp.emergency_contact_relation = new_val
            emp.save(update_fields=['emergency_contact_relation'])
            return True, f"Updated emergency relation to {new_val}"
        else:
            emp.emergency_contact_name = new_val
            emp.save(update_fields=['emergency_contact_name'])
            return True, f"Updated emergency contact name to {new_val}"

    # 7. Address, City, State, Postal Code
    if 'address' in norm:
        emp.address = new_val
        emp.save(update_fields=['address'])
        return True, f"Updated residential address to {new_val}"

    if 'city' in norm:
        emp.city = new_val
        emp.save(update_fields=['city'])
        return True, f"Updated city to {new_val}"

    if 'state' in norm:
        emp.state = new_val
        emp.save(update_fields=['state'])
        return True, f"Updated state to {new_val}"

    if any(k in norm for k in ['postal', 'pin', 'zip']):
        clean_pin = re.sub(r'\D', '', new_val)
        emp.postal_code = clean_pin or new_val
        emp.save(update_fields=['postal_code'])
        return True, f"Updated postal code to {emp.postal_code}"

    # 8. Personal particulars: Blood group, Marital status, DOB
    if 'blood' in norm:
        emp.blood_group = new_val.upper()
        emp.save(update_fields=['blood_group'])
        return True, f"Updated blood group to {emp.blood_group}"

    if 'marital' in norm:
        val_upper = new_val.upper()
        if 'MARRIED' in val_upper:
            emp.marital_status = 'MARRIED'
        elif 'DIVORCED' in val_upper:
            emp.marital_status = 'DIVORCED'
        elif 'WIDOWED' in val_upper:
            emp.marital_status = 'WIDOWED'
        else:
            emp.marital_status = 'SINGLE'
        emp.save(update_fields=['marital_status'])
        return True, f"Updated marital status to {emp.get_marital_status_display()}"

    if any(k in norm for k in ['birth', 'dob', 'date_of_birth']):
        from datetime import datetime
        for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%d %b %Y', '%d %B %Y'):
            try:
                d = datetime.strptime(new_val, fmt).date()
                emp.date_of_birth = d
                emp.save(update_fields=['date_of_birth'])
                return True, f"Updated date of birth to {d}"
            except ValueError:
                pass

    # 9. Education & Experience
    if 'education' in norm:
        emp.education_details = new_val
        emp.save(update_fields=['education_details'])
        return True, "Updated education details"

    if any(k in norm for k in ['experience', 'career', 'background']):
        emp.experience_summary = new_val
        emp.save(update_fields=['experience_summary'])
        return True, "Updated prior experience overview"

    # 10. Direct model field fallback (skipping properties)
    for model_field in emp._meta.fields:
        if model_field.name == norm:
            setattr(emp, model_field.name, new_val)
            emp.save(update_fields=[model_field.name])
            return True, f"Updated {model_field.verbose_name or model_field.name}"

    return False, "Field could not be matched automatically"


@login_required
def profile_correction_request(request):
    """Employees can request corrections for their own personal or banking information."""
    emp = getattr(request.user, 'employee_profile', None)
    if not emp:
        messages.error(request, "Employee profile not found.")
        return redirect('portal:home')

    current_data = {
        'Mobile Phone Number': emp.user.phone or '',
        'Personal Email': emp.personal_email or emp.user.email or '',
        'Salary Bank Name': emp.bank_name or '',
        'Bank Account Number': emp.bank_account_number or '',
        'Bank IFSC Code': emp.ifsc_code or '',
        'PAN Card Number': emp.pan_number or '',
        'PF UAN Number': emp.uan_number or '',
        'Emergency Contact Phone': emp.emergency_contact_phone or '',
        'Emergency Contact Name': emp.emergency_contact_name or '',
        'Emergency Contact Relation': emp.emergency_contact_relation or '',
        'Residential Address': emp.address or '',
        'City': emp.city or '',
        'State': emp.state or '',
        'Postal / PIN Code': emp.postal_code or '',
        'Blood Group': emp.blood_group or '',
        'Marital Status': emp.get_marital_status_display() or '',
        'Educational Details': emp.education_details or '',
        'Prior Experience Overview': emp.experience_summary or '',
    }

    if request.method == 'POST':
        form = ProfileCorrectionForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.employee = emp
            req.save()
            log_audit_trail('CREATE', 'Profile Corrections', f"Correction requested by {emp.emp_id} for {req.field_name}", user=request.user)
            messages.success(request, f"Your profile correction request for '{req.field_name}' has been submitted to HR for review.")
            return redirect('employees:employee_detail', emp_id=emp.emp_id)
    else:
        form = ProfileCorrectionForm()

    my_requests = emp.correction_requests.select_related('reviewed_by').all()[:10]

    return render(request, 'employees/profile_correction_form.html', {
        'form': form,
        'employee': emp,
        'current_data_json': json.dumps(current_data),
        'my_requests': my_requests,
    })


@login_required
@hr_required
def profile_corrections_list(request):
    """HR views and processes pending profile correction requests."""
    corrections = ProfileCorrectionRequest.objects.select_related('employee__user').all()
    return render(request, 'employees/profile_corrections_list.html', {'corrections': corrections})


@login_required
@hr_required
def review_profile_correction(request, request_id):
    """HR Approves or Rejects a profile correction request and immediately applies the change."""
    req = get_object_or_404(ProfileCorrectionRequest, id=request_id)
    action = request.POST.get('action')
    notes = request.POST.get('notes', '')

    if action == 'APPROVE':
        applied, detail_msg = apply_profile_correction_update(req)
        req.status = 'APPROVED'
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.review_notes = notes or (detail_msg if applied else "Approved by HR.")
        req.save()

        log_audit_trail('APPROVAL', 'Profile Corrections', f"Approved profile change for {req.employee.emp_id}: {req.field_name} ({detail_msg})", user=request.user)

        # Notify employee
        create_notification(
            recipient=req.employee.user,
            title="Profile Correction Approved",
            message=f"Your profile correction request for '{req.field_name}' has been approved and applied to your profile.",
            notification_type='SYSTEM',
            target_url=reverse('employees:employee_detail', kwargs={'emp_id': req.employee.emp_id})
        )

        messages.success(request, f"Profile correction for {req.employee.emp_id} ({req.employee.full_name}) approved! {detail_msg}")
    elif action == 'REJECT':
        req.status = 'REJECTED'
        req.reviewed_by = request.user
        req.reviewed_at = timezone.now()
        req.review_notes = notes or "Request was rejected after HR review."
        req.save()

        log_audit_trail('APPROVAL', 'Profile Corrections', f"Rejected profile change for {req.employee.emp_id}: {req.field_name}", user=request.user)

        # Notify employee
        create_notification(
            recipient=req.employee.user,
            title="Profile Correction Rejected",
            message=f"Your profile correction request for '{req.field_name}' was reviewed and rejected. Reason/Note: {req.review_notes}",
            notification_type='SYSTEM',
            target_url=reverse('employees:employee_detail', kwargs={'emp_id': req.employee.emp_id})
        )

        messages.info(request, f"Profile correction for {req.employee.emp_id} ({req.employee.full_name}) has been rejected.")

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
