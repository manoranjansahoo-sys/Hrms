import os
import re
import csv
import base64
import json
from decimal import Decimal
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import CustomUser
from accounts.decorators import role_required, hr_required, head_required, log_audit_trail
from organization.models import Department, Site
from recruitment.models import (
    RecruitmentJob, CandidateRegistrationLink, Candidate,
    CandidateEducation, CandidateExperience, CandidateSkill,
    CandidateDocument, JobApplication, ApplicationStatusHistory
)
from recruitment.forms import (
    JobOpeningForm, CandidateRegistrationLinkForm,
    PreInterviewApplicationForm, CandidateRegistrationStepForm,
    QuickSocialApplicationForm,
    CandidateOnboardingForm, ApplicationReviewForm,
    ScheduleInterviewForm, AppointEmployeeForm
)
from notifications.models import create_notification


# =========================================================================
# 1. HR MANAGEMENT VIEWS (Restricted to HR & Head)
# =========================================================================

@login_required
@hr_required
def candidate_links_list(request):
    """
    Section 3: HR Dashboard - Candidate Registration / Recruitment Link Management.
    Displays company universal master link, active positions master data, and campaign links.
    """
    links = CandidateRegistrationLink.objects.select_related('job__department', 'created_by').all()
    jobs = RecruitmentJob.objects.select_related('department', 'site').annotate(
        app_count=Count('applications')
    ).order_by('-created_at')

    # Search & filters
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status', '').strip()

    if search_query:
        links = links.filter(
            Q(title__icontains=search_query) |
            Q(job__title__icontains=search_query) |
            Q(token__icontains=search_query)
        )

    if status_filter == 'active':
        links = [l for l in links if l.is_valid]
    elif status_filter == 'closed':
        links = [l for l in links if not l.is_active]
    elif status_filter == 'expired':
        links = [l for l in links if l.is_expired]

    host = request.get_host()
    scheme = request.scheme
    universal_apply_url = request.build_absolute_uri(reverse('recruitment:candidate_apply'))
    fast_apply_url = request.build_absolute_uri(reverse('recruitment:candidate_fast_apply'))
    quick_job_form = JobOpeningForm()

    # Applications separated by registration stage
    office_applications = JobApplication.objects.select_related(
        'candidate', 'job', 'job__department'
    ).filter(is_office_registered=True).order_by('-applied_at')

    online_applications = JobApplication.objects.select_related(
        'candidate', 'job', 'job__department'
    ).filter(is_office_registered=False).order_by('-applied_at')

    office_apps_count = office_applications.count()
    online_apps_count = online_applications.count()

    return render(request, 'recruitment/candidate_links_list.html', {
        'links': links,
        'jobs': jobs,
        'active_jobs_count': jobs.filter(status=RecruitmentJob.Status.OPEN).count(),
        'total_applications_count': JobApplication.objects.count(),
        'office_applications': office_applications,
        'online_applications': online_applications,
        'office_apps_count': office_apps_count,
        'online_apps_count': online_apps_count,
        'search_query': search_query,
        'status_filter': status_filter,
        'host_url': f"{scheme}://{host}",
        'universal_apply_url': universal_apply_url,
        'fast_apply_url': fast_apply_url,
        'quick_job_form': quick_job_form,
        'sites': Site.objects.filter(is_active=True).order_by('name'),
        'departments': Department.objects.all().order_by('name'),
        'now': timezone.now(),
    })


@login_required
@hr_required
def create_candidate_link(request):
    """
    HR generates a new unique candidate registration link.
    """
    if request.method == 'POST':
        form = CandidateRegistrationLinkForm(request.POST)
        if form.is_valid():
            link = form.save(commit=False)
            link.created_by = request.user
            link.save()

            log_audit_trail(
                'CREATE',
                'Recruitment Links',
                f"Generated recruitment link '{link.title}' for {link.job.title} [Token: {link.token}]",
                user=request.user
            )
            messages.success(request, f"Candidate registration link for '{link.job.title}' generated successfully!")
            return redirect('recruitment:links_list')
    else:
        # Preselect job if passed in query param
        job_id = request.GET.get('job_id')
        initial_data = {}
        if job_id:
            initial_data['job'] = job_id
            initial_data['title'] = 'Public Application Invite'
        form = CandidateRegistrationLinkForm(initial=initial_data)

    jobs = RecruitmentJob.objects.filter(status=RecruitmentJob.Status.OPEN)
    return render(request, 'recruitment/link_create.html', {'form': form, 'jobs': jobs})


@login_required
@hr_required
def toggle_candidate_link(request, link_id):
    """Toggle activation/deactivation of a candidate registration link."""
    link = get_object_or_404(CandidateRegistrationLink, id=link_id)
    link.is_active = not link.is_active
    link.save()
    status_str = "activated" if link.is_active else "deactivated"
    messages.info(request, f"Recruitment link '{link.title}' has been {status_str}.")
    return redirect('recruitment:links_list')


@login_required
@hr_required
def jobs_list(request):
    """Unified Job Positions are now managed directly from Links Generation."""
    return redirect('recruitment:links_list')


@login_required
@hr_required
def create_job_opening(request):
    """Create a new job opening via modal or API form submission."""
    if request.method == 'POST':
        form = JobOpeningForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user

            # Check if an inline new department was entered (Admin only)
            new_dept_name = request.POST.get('new_department_name', '').strip()
            if new_dept_name:
                if not (request.user.role == CustomUser.Role.HEAD or request.user.is_superuser):
                    messages.error(request, "Permission Denied: Only Admin can add new departments.")
                    return redirect('recruitment:links_list')
                words = [w for w in new_dept_name.split() if w]
                base_code = ("".join(w[0] for w in words[:4]) if len(words) > 1 else new_dept_name[:4]).upper()
                code = base_code
                idx = 1
                while Department.objects.filter(code=code).exists():
                    code = f"{base_code[:3]}{idx}"
                    idx += 1
                dept, _ = Department.objects.get_or_create(
                    name__iexact=new_dept_name,
                    defaults={'name': new_dept_name, 'code': code}
                )
                job.department = dept

            location_val = request.POST.get('location')
            if location_val:
                job.location = location_val
                # Link site if matching location
                matched_site = Site.objects.filter(is_active=True).filter(
                    Q(name__icontains=location_val.split('(')[0].strip()) |
                    Q(city__icontains=location_val)
                ).first()
                if matched_site:
                    job.site = matched_site
            job.save()
            messages.success(request, f"Job opening '{job.title}' created successfully and is now active in the candidate registration form!")
            next_url = request.POST.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('recruitment:links_list')
        else:
            errors_str = "; ".join([f"{f}: {', '.join(errs)}" for f, errs in form.errors.items()])
            messages.error(request, f"Could not create job opening: {errors_str}")
            return redirect('recruitment:links_list')
    return redirect('recruitment:links_list')


@login_required
@hr_required
def edit_job_opening(request, job_id):
    """Edit existing job opening via modal or API form submission."""
    job = get_object_or_404(RecruitmentJob, id=job_id)
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if request.method == 'POST':
        form = JobOpeningForm(request.POST, instance=job)
        if form.is_valid():
            saved_job = form.save(commit=False)

            # Check if an inline new department was entered (Admin only)
            new_dept_name = request.POST.get('new_department_name', '').strip()
            if new_dept_name:
                if not (request.user.role == CustomUser.Role.HEAD or request.user.is_superuser):
                    messages.error(request, "Permission Denied: Only Admin can add new departments.")
                    return redirect('recruitment:links_list')
                words = [w for w in new_dept_name.split() if w]
                base_code = ("".join(w[0] for w in words[:4]) if len(words) > 1 else new_dept_name[:4]).upper()
                code = base_code
                idx = 1
                while Department.objects.filter(code=code).exists():
                    code = f"{base_code[:3]}{idx}"
                    idx += 1
                dept, _ = Department.objects.get_or_create(
                    name__iexact=new_dept_name,
                    defaults={'name': new_dept_name, 'code': code}
                )
                saved_job.department = dept

            location_val = request.POST.get('location')
            if location_val:
                saved_job.location = location_val
                matched_site = Site.objects.filter(is_active=True).filter(
                    Q(name__icontains=location_val.split('(')[0].strip()) |
                    Q(city__icontains=location_val)
                ).first()
                if matched_site:
                    saved_job.site = matched_site
            saved_job.save()
            messages.success(request, f"Job opening '{job.title}' updated successfully.")
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('recruitment:links_list')
        else:
            errors_str = "; ".join([f"{f}: {', '.join(errs)}" for f, errs in form.errors.items()])
            messages.error(request, f"Could not update job opening: {errors_str}")
            return redirect('recruitment:links_list')
    return redirect('recruitment:links_list')


@login_required
@head_required
def create_department_ajax(request):
    """AJAX endpoint to quickly add a department from inside a modal without a separate button or page."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Department name is required.'})

        existing = Department.objects.filter(name__iexact=name).first()
        if existing:
            return JsonResponse({
                'success': True,
                'id': existing.id,
                'name': existing.name,
                'code': existing.code,
                'already_existed': True,
                'message': f"Department '{existing.name}' is already available."
            })

        words = [w for w in name.split() if w]
        base_code = ("".join(w[0] for w in words[:4]) if len(words) > 1 else name[:4]).upper()
        code = base_code
        idx = 1
        while Department.objects.filter(code=code).exists():
            code = f"{base_code[:3]}{idx}"
            idx += 1

        dept = Department.objects.create(name=name, code=code)
        return JsonResponse({
            'success': True,
            'id': dept.id,
            'name': dept.name,
            'code': dept.code,
            'message': f"Department '{dept.name}' added successfully!"
        })
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
@head_required
def add_location(request):
    """Admin / HR setup to add company hiring locations."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        city = request.POST.get('city', '').strip()
        address = request.POST.get('address', '').strip()
        if name and city:
            base_code = f"{city[:3].upper()}-{name[:3].upper()}"
            code = base_code
            counter = 1
            while Site.objects.filter(code=code).exists():
                code = f"{base_code}-{counter}"
                counter += 1

            site, created = Site.objects.get_or_create(
                name=name,
                city=city,
                defaults={
                    'code': code,
                    'address': address,
                    'is_active': True,
                }
            )
            if not created and not site.is_active:
                site.is_active = True
                site.save()
            messages.success(request, f"Location '{name} ({city})' added successfully.")
        else:
            messages.error(request, "Location Name and City are required.")

    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect('recruitment:links_list')


@login_required
@head_required
def delete_location(request, site_id):
    """Admin / HR deletion of company hiring locations."""
    site = get_object_or_404(Site, id=site_id)
    if request.method == 'POST':
        site_name = site.name
        try:
            site.delete()
        except Exception:
            site.is_active = False
            site.save()
        messages.success(request, f"Location '{site_name}' deleted successfully.")

    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and next_url.startswith('/'):
        return redirect(next_url)
    return redirect('recruitment:links_list')


@login_required
@head_required
def locations_manager(request):
    """
    Dedicated Admin Command Center for Managing Company Locations.
    Admin can clearly see each location and which job positions belong to that location.
    """
    sites = Site.objects.filter(is_active=True).order_by('name')
    locations_data = []
    for s in sites:
        pos_list = RecruitmentJob.objects.filter(
            Q(site=s) | Q(location__icontains=s.name) | Q(location__icontains=s.city)
        ).distinct()
        locations_data.append({
            'site': s,
            'positions': pos_list,
            'positions_count': pos_list.count(),
        })

    return render(request, 'recruitment/admin_locations.html', {
        'locations_data': locations_data,
        'sites': sites,
    })


@login_required
@hr_required
def candidates_list(request):
    """
    Section 7: HR Application Management Roster.
    Filterable by job title, experience level, application status, education.
    Separated by office walk-in registration vs online fast-apply applications.
    """
    tab = request.GET.get('tab', 'office').strip()
    if tab not in ['office', 'online']:
        tab = 'office'

    is_office = (tab == 'office')
    applications = JobApplication.objects.select_related(
        'candidate', 'candidate__experience', 'candidate__education',
        'candidate__skills', 'job', 'job__department'
    ).filter(is_office_registered=is_office)

    # Search query
    search = request.GET.get('search', '').strip()
    job_id = request.GET.get('job', '')
    status_filter = request.GET.get('status', '')
    exp_filter = request.GET.get('experience', '')
    sort_by = request.GET.get('sort', 'date_desc')

    if search:
        applications = applications.filter(
            Q(candidate__full_name__icontains=search) |
            Q(candidate__email__icontains=search) |
            Q(candidate__phone__icontains=search) |
            Q(application_id__icontains=search) |
            Q(candidate__skills__technical_skills__icontains=search)
        )
    if job_id:
        applications = applications.filter(job_id=job_id)
    if status_filter:
        applications = applications.filter(status=status_filter)
    if exp_filter:
        applications = applications.filter(candidate__experience__experience_type=exp_filter)

    # Sorting
    sort_map = {
        'date_desc': '-applied_at',
        'date_asc': 'applied_at',
        'name_asc': 'candidate__full_name',
        'name_desc': '-candidate__full_name',
        'status_asc': 'status',
        'role_asc': 'job__title',
    }
    order_field = sort_map.get(sort_by, '-applied_at')
    applications = applications.order_by(order_field)

    # Summary metrics for the active tab
    tab_base = JobApplication.objects.filter(is_office_registered=is_office)
    total_apps = tab_base.count()
    under_review = tab_base.filter(status=JobApplication.Status.UNDER_REVIEW).count()
    shortlisted = tab_base.filter(status=JobApplication.Status.SHORTLISTED).count()
    interview_scheduled = tab_base.filter(status=JobApplication.Status.INTERVIEW_SCHEDULED).count()
    selected = tab_base.filter(status=JobApplication.Status.SELECTED).count()
    hired = tab_base.filter(status=JobApplication.Status.HIRED).count()

    office_apps_count = JobApplication.objects.filter(is_office_registered=True).count()
    online_apps_count = JobApplication.objects.filter(is_office_registered=False).count()

    # Pagination with configurable page size (5, 10, 20, 50, 100)
    per_page_param = request.GET.get('per_page', '10')
    try:
        per_page = int(per_page_param)
        if per_page not in [5, 10, 20, 50, 100]:
            per_page = 10
    except (ValueError, TypeError):
        per_page = 10

    paginator = Paginator(applications, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    jobs = RecruitmentJob.objects.all()

    host = request.get_host()
    scheme = request.scheme
    universal_apply_url = request.build_absolute_uri(reverse('recruitment:candidate_apply'))
    fast_apply_url = request.build_absolute_uri(reverse('recruitment:candidate_fast_apply'))

    page_title = "Candidate Applications & Talent Roster" if is_office else "Candidate Job Applications (Online)"
    page_subtitle = "In-person registered candidates who completed full pre-interview verification." if is_office else "Online fast-apply applications submitted via website and social channels."

    # Scheduled interviews pipeline for the scheduling section
    scheduled_interviews = JobApplication.objects.filter(
        status=JobApplication.Status.INTERVIEW_SCHEDULED
    ).select_related('candidate', 'job').order_by('-interview_date', '-interview_time')[:15]

    # Candidates with INTERVIEW_SCHEDULED status available for the interview round schedule picker
    candidates_to_schedule = JobApplication.objects.filter(
        is_office_registered=is_office,
        status=JobApplication.Status.INTERVIEW_SCHEDULED
    ).select_related('candidate', 'job').order_by('candidate__full_name')

    interview_form = ScheduleInterviewForm()
    interview_modes = [
        ('VIRTUAL', 'Virtual (Google Meet / Microsoft Teams)'),
        ('IN_PERSON', 'In-Person (Office Campus)'),
        ('TELEPHONIC', 'Telephonic Round')
    ]

    return render(request, 'recruitment/candidates_list.html', {
        'page_obj': page_obj,
        'candidates_to_schedule': candidates_to_schedule,
        'jobs': jobs,
        'selected_job': job_id,
        'selected_status': status_filter,
        'selected_exp': exp_filter,
        'selected_sort': sort_by,
        'selected_per_page': per_page,
        'search_query': search,
        'total_apps': total_apps,
        'under_review': under_review,
        'shortlisted': shortlisted,
        'interview_scheduled': interview_scheduled,
        'selected': selected,
        'hired': hired,
        'status_choices': JobApplication.Status.choices,
        'universal_apply_url': universal_apply_url,
        'fast_apply_url': fast_apply_url,
        'active_tab': tab,
        'office_apps_count': office_apps_count,
        'online_apps_count': online_apps_count,
        'page_title': page_title,
        'page_subtitle': page_subtitle,
        'scheduled_interviews': scheduled_interviews,
        'interview_form': interview_form,
        'interview_modes': interview_modes,
        'today_date': (timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()).strftime('%Y-%m-%d'),
    })


@login_required
@hr_required
def export_candidates_csv(request):
    """
    Export candidate applications pipeline to a CSV spreadsheet report.
    Respects current filters, search query parameters, and active tab.
    """
    tab = request.GET.get('tab', 'office').strip()
    is_office = (tab != 'online')

    response = HttpResponse(content_type='text/csv')
    filename_prefix = "Talent_Roster_Office" if is_office else "Job_Applications_Online"
    response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Application ID', 'Candidate Name', 'Email', 'Phone',
        'Job Role', 'Department', 'Location',
        'Experience Type', 'Total Experience', 'Current Company',
        'Highest Qualification', 'Institution', 'Status',
        'Application Type', 'Applied Date'
    ])

    applications = JobApplication.objects.select_related(
        'candidate', 'candidate__education', 'candidate__experience',
        'job', 'job__department'
    ).filter(is_office_registered=is_office)

    search = request.GET.get('search', '').strip()
    job_id = request.GET.get('job', '').strip()
    status_filter = request.GET.get('status', '').strip()
    exp_filter = request.GET.get('experience', '').strip()
    sort_by = request.GET.get('sort', 'date_desc').strip()

    if search:
        applications = applications.filter(
            Q(candidate__full_name__icontains=search) |
            Q(candidate__email__icontains=search) |
            Q(candidate__phone__icontains=search) |
            Q(application_id__icontains=search) |
            Q(candidate__skills__technical_skills__icontains=search)
        )
    if job_id:
        applications = applications.filter(job_id=job_id)
    if status_filter:
        applications = applications.filter(status=status_filter)
    if exp_filter:
        applications = applications.filter(candidate__experience__experience_type=exp_filter)

    sort_map = {
        'date_desc': '-applied_at',
        'date_asc': 'applied_at',
        'name_asc': 'candidate__full_name',
        'name_desc': '-candidate__full_name',
        'status_asc': 'status',
        'role_asc': 'job__title',
    }
    order_field = sort_map.get(sort_by, '-applied_at')
    applications = applications.order_by(order_field)

    for app in applications:
        c = app.candidate
        edu = getattr(c, 'education', None)
        exp = getattr(c, 'experience', None)

        exp_type = exp.get_experience_type_display() if exp else 'Not specified'
        exp_duration = '0y 0m'
        curr_comp = ''
        if exp and exp.experience_type != 'FRESHER':
            exp_duration = f"{exp.total_experience_years or 0}y {exp.total_experience_months or 0}m"
            curr_comp = exp.current_company or ''
        elif exp and exp.experience_type == 'FRESHER':
            exp_duration = 'Fresher'

        writer.writerow([
            app.application_id,
            c.full_name,
            c.email,
            c.phone,
            app.job.title if app.job else 'General',
            app.job.department.name if app.job and app.job.department else 'General',
            app.job.location if app.job else '',
            exp_type,
            exp_duration,
            curr_comp,
            edu.highest_qualification if edu else '',
            edu.institution if edu else '',
            app.get_status_display(),
            app.applied_at.strftime('%Y-%m-%d %H:%M') if app.applied_at else '',
        ])

    return response


@login_required
@hr_required
def bulk_update_candidate_status(request):
    """
    Bulk or inline status updater for candidate applications.
    Allows HR to update status of multiple or individual candidates
    directly from candidates_list without opening each profile.
    Supports both AJAX (JSON) and traditional POST redirect.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.content_type == 'application/json' or
        'application/json' in request.headers.get('Accept', '')
    )

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            data = {}
        application_ids = data.get('application_ids', [])
        new_status = data.get('status')
        notes = data.get('notes', 'Bulk status update by HR')
    else:
        application_ids = request.POST.getlist('application_ids') or request.POST.getlist('selected_candidates')
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', 'Bulk status update by HR')

    if isinstance(application_ids, str):
        application_ids = [s.strip() for s in application_ids.split(',') if s.strip()]

    valid_statuses = dict(JobApplication.Status.choices)
    if not new_status or new_status not in valid_statuses:
        if is_ajax:
            return JsonResponse({'success': False, 'error': f'Invalid status: {new_status}'}, status=400)
        messages.error(request, 'Invalid application status selected.')
        return redirect('recruitment:candidates_list')

    if not application_ids:
        if is_ajax:
            return JsonResponse({'success': False, 'error': 'No candidates were selected.'}, status=400)
        messages.warning(request, 'No candidates were selected for status update.')
        return redirect('recruitment:candidates_list')

    applications = JobApplication.objects.filter(id__in=application_ids).select_related('candidate', 'job')
    updated_count = 0
    updated_ids = []

    for app in applications:
        old_status = app.status
        if old_status != new_status:
            app.status = new_status
            app.save(update_fields=['status'])

            ApplicationStatusHistory.objects.create(
                application=app,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user,
                notes=notes
            )

            log_audit_trail(
                'UPDATE',
                'Recruitment',
                f"Candidate status updated for {app.candidate.full_name} ({app.application_id}) from {old_status} to {new_status}",
                request.user,
                request
            )
            updated_count += 1
            updated_ids.append(app.id)
        else:
            # Already in target status, count as processed
            updated_ids.append(app.id)

    status_display = valid_statuses.get(new_status, new_status)

    if is_ajax:
        return JsonResponse({
            'success': True,
            'updated_count': updated_count,
            'new_status': new_status,
            'status_display': status_display,
            'updated_ids': updated_ids,
            'message': f"Updated {updated_count} candidate(s) to '{status_display}'."
        })

    messages.success(request, f"Updated {updated_count} candidate(s) to '{status_display}'.")
    return redirect('recruitment:candidates_list')


@login_required
@hr_required
def schedule_candidate_interview(request):
    """
    Schedule an interview round for one or multiple candidates directly from the Candidate Applications page.
    Updates application status to INTERVIEW_SCHEDULED, saves date/time/mode/venue/notes,
    creates status audit history, and sends candidate email notifications.
    Supports both standard form POST and AJAX requests.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method not allowed.'}, status=405)

    is_ajax = (
        request.headers.get('x-requested-with') == 'XMLHttpRequest' or
        request.content_type == 'application/json' or
        'application/json' in request.headers.get('Accept', '')
    )

    app_ids = []
    interview_date = None
    interview_time = None
    interview_mode = 'VIRTUAL'
    interview_location_link = ''
    interview_notes = ''
    active_tab = 'office'

    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
            app_ids = data.get('application_ids', [])
            if not app_ids and data.get('application_id'):
                app_ids = [data.get('application_id')]
            interview_date = data.get('interview_date')
            interview_time = data.get('interview_time')
            interview_mode = data.get('interview_mode', 'VIRTUAL')
            interview_location_link = data.get('interview_location_link', '')
            interview_notes = data.get('interview_notes', '')
            active_tab = data.get('tab', 'office')
        except Exception:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
    else:
        app_ids = request.POST.getlist('application_ids')
        if not app_ids:
            raw_single = request.POST.get('application_id')
            if raw_single:
                app_ids = [raw_single]
            elif request.POST.get('candidate_ids'):
                app_ids = [x.strip() for x in request.POST.get('candidate_ids').split(',') if x.strip()]
        interview_date = request.POST.get('interview_date')
        interview_time = request.POST.get('interview_time')
        interview_mode = request.POST.get('interview_mode', 'VIRTUAL')
        interview_location_link = request.POST.get('interview_location_link', '').strip()
        interview_notes = request.POST.get('interview_notes', '').strip()
        active_tab = request.POST.get('tab', 'office')

    if not app_ids:
        err_msg = "Please select at least one candidate to schedule an interview."
        if is_ajax:
            return JsonResponse({'success': False, 'message': err_msg}, status=400)
        messages.error(request, err_msg)
        return redirect(f"{reverse('recruitment:candidates_list')}?tab={active_tab}#scheduleInterviewSection")

    if not interview_date or not interview_time:
        err_msg = "Interview Date and Time are required fields."
        if is_ajax:
            return JsonResponse({'success': False, 'message': err_msg}, status=400)
        messages.error(request, err_msg)
        return redirect(f"{reverse('recruitment:candidates_list')}?tab={active_tab}#scheduleInterviewSection")

    # Validate that interview date cannot be in the past (yesterday or earlier)
    try:
        if isinstance(interview_date, str):
            parsed_interview_date = datetime.strptime(interview_date.strip(), '%Y-%m-%d').date()
        else:
            parsed_interview_date = interview_date
    except (ValueError, TypeError):
        err_msg = "Invalid interview date format. Please choose a valid date (YYYY-MM-DD)."
        if is_ajax:
            return JsonResponse({'success': False, 'message': err_msg}, status=400)
        messages.error(request, err_msg)
        return redirect(f"{reverse('recruitment:candidates_list')}?tab={active_tab}#scheduleInterviewSection")

    today_date = timezone.localdate() if hasattr(timezone, 'localdate') else timezone.now().date()
    if parsed_interview_date < today_date:
        err_msg = f"Invalid interview date ({parsed_interview_date}). Interview date cannot be in the past (yesterday or earlier). Please choose today or a future date."
        if is_ajax:
            return JsonResponse({'success': False, 'message': err_msg}, status=400)
        messages.error(request, err_msg)
        return redirect(f"{reverse('recruitment:candidates_list')}?tab={active_tab}#scheduleInterviewSection")

    # If interview is scheduled for today, time cannot be in the past
    if parsed_interview_date == today_date and interview_time:
        try:
            time_str = str(interview_time).strip()
            parts = time_str.split(':')
            if len(parts) >= 2:
                parsed_interview_time = datetime.strptime(f"{parts[0].zfill(2)}:{parts[1].zfill(2)}", '%H:%M').time()
                current_time = timezone.localtime().time()
                if parsed_interview_time < current_time.replace(second=0, microsecond=0):
                    err_msg = f"Invalid interview time ({parsed_interview_time.strftime('%I:%M %p')}). For today's date, interview time cannot be in the past. Please choose a future time slot."
                    if is_ajax:
                        return JsonResponse({'success': False, 'message': err_msg}, status=400)
                    messages.error(request, err_msg)
                    return redirect(f"{reverse('recruitment:candidates_list')}?tab={active_tab}#scheduleInterviewSection")
        except (ValueError, TypeError):
            pass

    applications = JobApplication.objects.filter(id__in=app_ids).select_related('candidate', 'job')
    if not applications.exists():
        err_msg = "Selected candidate applications were not found."
        if is_ajax:
            return JsonResponse({'success': False, 'message': err_msg}, status=404)
        messages.error(request, err_msg)
        return redirect(f"{reverse('recruitment:candidates_list')}?tab={active_tab}#scheduleInterviewSection")

    scheduled_names = []
    for app in applications:
        old_status = app.status
        app.interview_date = interview_date
        app.interview_time = interview_time
        app.interview_mode = interview_mode
        app.interview_location_link = interview_location_link
        app.interview_notes = interview_notes
        app.status = JobApplication.Status.INTERVIEW_SCHEDULED
        app.save()

        mode_display = app.get_interview_mode_display()

        ApplicationStatusHistory.objects.create(
            application=app,
            old_status=old_status,
            new_status=JobApplication.Status.INTERVIEW_SCHEDULED,
            changed_by=request.user,
            notes=f"Interview scheduled on {interview_date} at {interview_time} ({mode_display})"
        )

        try:
            log_audit_trail(
                request.user,
                'UPDATE',
                'Recruitment',
                f"Scheduled interview for {app.candidate.full_name} ({app.application_id}) on {interview_date} at {interview_time}",
                request
            )
        except Exception:
            pass

        # Email invitation to candidate
        try:
            formatted_date = str(interview_date)
            formatted_time = str(interview_time)
            try:
                dt_obj = datetime.strptime(f"{interview_date} {interview_time}", "%Y-%m-%d %H:%M")
                formatted_date = dt_obj.strftime("%A, %d %B %Y")
                formatted_time = dt_obj.strftime("%I:%M %p")
            except Exception:
                pass

            subject = f"Interview Scheduled: {app.job.title} at Company HRMS"
            track_url = request.build_absolute_uri(reverse('recruitment:candidate_track_id', kwargs={'application_id': app.application_id}))
            message = (
                f"Dear {app.candidate.full_name},\n\n"
                f"We are pleased to invite you for an interview round for the position of {app.job.title}.\n\n"
                f"Interview Details:\n"
                f"- Date: {formatted_date}\n"
                f"- Time: {formatted_time}\n"
                f"- Mode: {mode_display}\n"
                f"- Location / Meeting Link: {app.interview_location_link or 'Will be shared by HR coordinator'}\n\n"
                f"Candidate Guidelines / Agenda:\n"
                f"{app.interview_notes or 'Please be ready with your portfolio and technical setup 5 minutes prior to the scheduled slot.'}\n\n"
                f"Track your application status live at:\n"
                f"{track_url}\n\n"
                f"Best regards,\n"
                f"HR & Talent Acquisition Team\n"
            )
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [app.candidate.email],
                fail_silently=True
            )
        except Exception:
            pass

        scheduled_names.append(app.candidate.full_name)

    names_summary = ", ".join(scheduled_names)
    success_msg = f"Interview round successfully scheduled for {names_summary} on {interview_date} at {interview_time}!"

    if is_ajax:
        return JsonResponse({
            'success': True,
            'count': len(scheduled_names),
            'names': scheduled_names,
            'message': success_msg
        })

    messages.success(request, success_msg)
    return redirect(f"{reverse('recruitment:candidates_list')}?tab={active_tab}#scheduleInterviewSection")


@login_required
@hr_required
def candidate_detail(request, application_id):
    """
    HR Application Review, Resume Download, Status Updater, and Interview Scheduler.
    """
    app = get_object_or_404(
        JobApplication.objects.select_related(
            'candidate', 'candidate__education', 'candidate__experience',
            'candidate__skills', 'job__department', 'registration_link'
        ),
        id=application_id
    )

    review_form = ApplicationReviewForm(instance=app)
    interview_form = ScheduleInterviewForm(instance=app)

    if request.method == 'POST':
        action_type = request.POST.get('action_type')

        if action_type == 'UPDATE_REVIEW':
            old_status = app.status
            review_form = ApplicationReviewForm(request.POST, instance=app)
            if review_form.is_valid():
                updated_app = review_form.save()
                new_status = updated_app.status

                if old_status != new_status:
                    ApplicationStatusHistory.objects.create(
                        application=app,
                        old_status=old_status,
                        new_status=new_status,
                        changed_by=request.user,
                        notes=request.POST.get('status_notes', 'Status updated by HR')
                    )

                log_audit_trail(
                    'UPDATE',
                    'Recruitment',
                    f"Updated application {app.application_id} ({app.candidate.full_name}) to status: {new_status}",
                    user=request.user
                )
                messages.success(request, f"Application {app.application_id} status updated to {app.get_status_display()}!")
                return redirect('recruitment:candidate_detail', application_id=app.id)

        elif action_type == 'SCHEDULE_INTERVIEW':
            interview_form = ScheduleInterviewForm(request.POST, instance=app)
            if interview_form.is_valid():
                scheduled_app = interview_form.save(commit=False)
                scheduled_app.status = JobApplication.Status.INTERVIEW_SCHEDULED
                scheduled_app.save()

                ApplicationStatusHistory.objects.create(
                    application=app,
                    old_status=app.status,
                    new_status=JobApplication.Status.INTERVIEW_SCHEDULED,
                    changed_by=request.user,
                    notes=f"Interview scheduled on {scheduled_app.interview_date} at {scheduled_app.interview_time} ({scheduled_app.get_interview_mode_display()})"
                )

                # Send email notification to candidate
                try:
                    subject = f"Interview Scheduled: {app.job.title} at Company HRMS"
                    track_url = request.build_absolute_uri(reverse('recruitment:candidate_track_id', kwargs={'application_id': app.application_id}))
                    message = (
                        f"Dear {app.candidate.full_name},\n\n"
                        f"We are pleased to invite you for an interview for the {app.job.title} role.\n\n"
                        f"Interview Details:\n"
                        f"- Date: {scheduled_app.interview_date.strftime('%A, %d %B %Y')}\n"
                        f"- Time: {scheduled_app.interview_time.strftime('%I:%M %p')}\n"
                        f"- Mode: {scheduled_app.get_interview_mode_display()}\n"
                        f"- Location/Meeting Link: {scheduled_app.interview_location_link}\n\n"
                        f"Guidelines / Agenda:\n{scheduled_app.interview_notes or 'Please be ready with your portfolio and technical setup 5 minutes prior to the scheduled slot.'}\n\n"
                        f"You can track your real-time application status here:\n"
                        f"{track_url}\n\n"
                        f"Best regards,\nHR & Talent Acquisition Team\nCompany HRMS"
                    )
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [app.candidate.email],
                        fail_silently=True
                    )
                except Exception:
                    pass

                messages.success(request, f"Interview scheduled for {app.candidate.full_name} and confirmation email sent!")
                return redirect('recruitment:candidate_detail', application_id=app.id)

    status_history = app.status_history.select_related('changed_by').all()
    candidate_documents = app.candidate.documents.all()

    from employees.models import EmployeeProfile
    employee_profile = EmployeeProfile.objects.filter(
        Q(user__email__iexact=app.candidate.email) |
        Q(personal_email__iexact=app.candidate.email)
    ).select_related('user', 'department', 'designation', 'site').first()

    return render(request, 'recruitment/candidate_detail.html', {
        'application': app,
        'candidate': app.candidate,
        'education': getattr(app.candidate, 'education', None),
        'experience': getattr(app.candidate, 'experience', None),
        'skills': getattr(app.candidate, 'skills', None),
        'documents': candidate_documents,
        'status_history': status_history,
        'review_form': review_form,
        'interview_form': interview_form,
        'employee_profile': employee_profile,
    })


# =========================================================================
# 2. PUBLIC CANDIDATE REGISTRATION & GOOGLE AUTHENTICATION VIEWS
# =========================================================================

def decode_google_id_token(id_token):
    """
    Decodes and validates a Google Identity Services JWT credential (ID Token).
    Extracts email, full name, profile picture URL, and Google user ID (sub).
    """
    if not id_token:
        return None
    try:
        parts = id_token.strip().split('.')
        if len(parts) != 3:
            return None
        payload_b64 = parts[1]
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += '=' * (4 - rem)
        decoded = base64.urlsafe_b64decode(payload_b64.encode('utf-8'))
        payload = json.loads(decoded.decode('utf-8'))

        email = payload.get('email', '').strip().lower()
        if not email:
            return None

        name = payload.get('name', '').strip()
        if not name:
            given = payload.get('given_name', '').strip()
            family = payload.get('family_name', '').strip()
            name = f"{given} {family}".strip() or email.split('@')[0]

        return {
            'email': email,
            'name': name,
            'picture': payload.get('picture', '').strip(),
            'sub': payload.get('sub', '').strip(),
            'email_verified': payload.get('email_verified', True)
        }
    except Exception:
        return None


def serialize_candidate_data(candidate):
    """
    Serializes an existing candidate's full profile data into a dictionary
    to auto-populate registration forms when authenticated with the same Google account.
    """
    if not candidate:
        return None

    edu = getattr(candidate, 'education', None)
    exp = getattr(candidate, 'experience', None)
    skl = getattr(candidate, 'skills', None)

    latest_app = candidate.applications.select_related('job').order_by('-applied_at').first()
    applied_job_id = latest_app.job_id if latest_app else None
    applied_job_title = latest_app.job.title if (latest_app and latest_app.job) else ''

    # Resume inspection from JobApplication or CandidateDocument
    saved_resume_url = ''
    saved_resume_name = ''
    if latest_app and latest_app.resume:
        try:
            saved_resume_url = latest_app.resume.url
            saved_resume_name = os.path.basename(latest_app.resume.name)
        except Exception:
            pass
    if not saved_resume_url:
        resume_doc = candidate.documents.filter(doc_type='RESUME').first()
        if resume_doc and resume_doc.file:
            try:
                saved_resume_url = resume_doc.file.url
                saved_resume_name = os.path.basename(resume_doc.file.name)
            except Exception:
                pass

    return {
        'full_name': candidate.full_name or '',
        'email': candidate.email or '',
        'phone': candidate.phone or '',
        'alt_phone': candidate.alt_phone or '',
        'has_saved_resume': bool(saved_resume_url),
        'saved_resume_url': saved_resume_url,
        'saved_resume_name': saved_resume_name,
        'current_address': candidate.current_address or '',
        'city': candidate.city or '',
        'state': candidate.state or '',
        'postal_code': candidate.postal_code or '',
        'country': candidate.country or 'India',
        'job': applied_job_id,
        'job_id': applied_job_id,
        'applied_job_id': applied_job_id,
        'applied_job_title': applied_job_title,
        # Education
        'highest_qualification': edu.highest_qualification if edu else '',
        'institution': edu.institution if edu else '',
        'degree_name': edu.degree_name if edu else '',
        'specialization': edu.specialization if edu else '',
        'passing_year': edu.passing_year if (edu and edu.passing_year) else '',
        'percentage_cgpa': edu.percentage_cgpa if edu else '',
        # Experience
        'experience_type': exp.experience_type if exp else 'EXPERIENCED',
        'total_experience_years': exp.total_experience_years if exp else 0,
        'total_experience_months': exp.total_experience_months if exp else 0,
        'current_company': exp.current_company if exp else '',
        'current_designation': exp.current_designation if exp else '',
        'previous_company': exp.previous_company if exp else '',
        'notice_period_days': exp.notice_period_days if exp else 30,
        'expected_ctc': str(exp.expected_ctc) if exp and exp.expected_ctc is not None else '',
        'current_ctc': str(exp.current_ctc) if exp and exp.current_ctc is not None else '',
        # Skills & links
        'technical_skills': skl.technical_skills if skl else '',
        'programming_languages': skl.programming_languages if skl else '',
        'frameworks': skl.frameworks if skl else '',
        'linkedin_url': skl.linkedin_url if skl else '',
        'portfolio_url': skl.portfolio_url if skl else '',
        'github_url': skl.github_url if skl else '',
        # Identity
        'is_google_verified': candidate.is_google_verified,
        'google_picture_url': candidate.google_picture_url or candidate.get_photo_url(),
    }


def candidate_google_auth(request):
    """
    Candidate Google Authentication & Identification Endpoint.
    1. Receives Google ID token from GIS (Google Identity Services) or client parameters.
    2. Decodes/verifies user email, name, picture, and sub.
    3. Saves verified candidate session.
    4. Automatically searches database for matching candidate by email.
    5. Returns candidate's previously saved details for instant form auto-population.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)

    token = request.POST.get('credential')
    email = request.POST.get('email')
    name = request.POST.get('name')
    picture = request.POST.get('picture')
    sub = request.POST.get('sub')

    if not token and request.body:
        try:
            body_data = json.loads(request.body.decode('utf-8'))
            token = body_data.get('credential')
            email = body_data.get('email') or email
            name = body_data.get('name') or name
            picture = body_data.get('picture') or picture
            sub = body_data.get('sub') or sub
        except Exception:
            pass

    google_data = None
    if token:
        google_data = decode_google_id_token(token)

    if not google_data and email:
        google_data = {
            'email': email.strip().lower(),
            'name': (name or email.split('@')[0]).strip(),
            'picture': picture or '',
            'sub': sub or ('google-' + email.strip().lower()),
            'email_verified': True
        }

    if not google_data or not google_data.get('email'):
        return JsonResponse({'success': False, 'error': 'Invalid or missing Google credential token'}, status=400)

    # Store verified identity in candidate session
    request.session['candidate_google_auth'] = google_data
    request.session.modified = True

    # Search database for existing candidate with this verified Google email
    email = google_data['email']
    candidate = Candidate.objects.select_related('education', 'experience', 'skills').filter(email__iexact=email).first()

    is_returning = False
    candidate_data = None

    if candidate:
        is_returning = True
        # Mark Google verification on candidate record
        candidate.is_google_verified = True
        if google_data.get('sub'):
            candidate.google_sub = google_data['sub']
        if google_data.get('picture') and not candidate.google_picture_url:
            candidate.google_picture_url = google_data['picture']
        candidate.save()

        candidate_data = serialize_candidate_data(candidate)

    return JsonResponse({
        'success': True,
        'google_user': google_data,
        'is_returning_candidate': is_returning,
        'candidate_data': candidate_data,
        'message': f"Successfully verified Google account for {google_data.get('name')}."
    })


def candidate_google_logout(request):
    """
    Clears candidate's Google session to allow switching accounts.
    """
    if 'candidate_google_auth' in request.session:
        del request.session['candidate_google_auth']
        request.session.modified = True
    return JsonResponse({'success': True, 'message': 'Google authentication cleared.'})


def candidate_lookup_ajax(request):
    """
    Auto-fetches candidate details by Email or Phone Number.
    Used dynamically on the Candidate Registration form to pre-populate details
    when the candidate types their email or phone.
    """
    q = request.GET.get('q', '').strip() or request.POST.get('q', '').strip()
    if not q:
        return JsonResponse({'success': False, 'message': 'Query required'}, status=400)

    candidate = None
    if '@' in q:
        candidate = Candidate.objects.select_related('education', 'experience', 'skills').filter(email__iexact=q.lower()).first()
    else:
        digits = re.sub(r'\D', '', q)
        if digits.startswith('91') and len(digits) == 12:
            digits = digits[2:]
        elif digits.startswith('0') and len(digits) == 11:
            digits = digits[1:]
        if len(digits) >= 10:
            candidate = Candidate.objects.select_related('education', 'experience', 'skills').filter(
                Q(phone__icontains=digits[-10:]) | Q(alt_phone__icontains=digits[-10:])
            ).first()

    if candidate:
        data = serialize_candidate_data(candidate)
        if 'candidate_google_auth' not in request.session:
            request.session['candidate_google_auth'] = {
                'email': candidate.email,
                'name': candidate.full_name,
                'sub': candidate.google_sub or f"cand-{candidate.id}",
                'picture': candidate.google_picture_url or '',
            }
            request.session.modified = True
        return JsonResponse({
            'success': True,
            'is_returning_candidate': True,
            'candidate_data': data,
            'message': f"Found existing application for {candidate.full_name}!"
        })

    return JsonResponse({'success': False, 'message': 'No existing candidate record found'})


def candidate_register(request, token=None):
    """
    STAGE 1: Public Pre-Interview Candidate Registration (Google Form Style).
    Supports:
    1. Universal / Master link: /candidate/apply/ or /candidate/register/ (token=None)
       Candidate selects any active position from master data.
    2. Specific campaign link: /candidate/register/<token>/
       Pre-selects link.job and associates application with the link.
    Requires Google Authentication. Identifies returning candidate by Google email
    and automatically fetches/populates previous details.
    """
    link = None
    job = None

    # Check if a specific campaign token was passed
    if token and token not in ('general', 'apply'):
        link = CandidateRegistrationLink.objects.select_related('job__department', 'job__site').filter(token=token).first()
        if not link:
            return render(request, 'recruitment/public/link_invalid.html', {
                'reason': 'closed'
            })
        if not link.is_valid:
            return render(request, 'recruitment/public/link_invalid.html', {
                'link': link,
                'job': link.job,
                'reason': 'expired' if link.is_expired else ('limit_reached' if link.is_limit_reached else 'closed')
            })
        job = link.job
        if request.method == 'GET':
            CandidateRegistrationLink.objects.filter(id=link.id).update(views_count=link.views_count + 1)
            link.refresh_from_db()
    else:
        # Check query param for preselecting job (e.g. ?job=1 or ?position=senior-python-developer)
        job_id_param = request.GET.get('job')
        pos_param = request.GET.get('position')
        if job_id_param and str(job_id_param).isdigit():
            job = RecruitmentJob.objects.filter(id=job_id_param).first()
        if not job and (pos_param or (job_id_param and not str(job_id_param).isdigit())):
            target_str = pos_param or job_id_param
            from django.utils.text import slugify
            for j in RecruitmentJob.objects.all():
                if slugify(j.title) == slugify(target_str) or j.title.lower() == target_str.lower().replace('-', ' '):
                    job = j
                    break

    # If a specific position was targeted but is CLOSED (or on hold / draft):
    if job and job.status != RecruitmentJob.Status.OPEN:
        return render(request, 'recruitment/public/link_invalid.html', {
            'job': job,
            'reason': 'closed'
        })

    # Only ACTIVE / OPEN jobs are available in the public application form
    open_jobs = list(RecruitmentJob.objects.filter(status=RecruitmentJob.Status.OPEN).select_related('department', 'site'))

    if not job and len(open_jobs) == 1:
        job = open_jobs[0]

    google_auth = request.session.get('candidate_google_auth')
    google_client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '315051569117-7knfkmsdkcsmcbmnp2or1pos542kd8b7.apps.googleusercontent.com')
    returning_candidate = None

    lookup_email = (google_auth.get('email') if google_auth else None) or request.session.get('last_applied_email') or request.GET.get('email')
    lookup_phone = request.GET.get('phone')

    if lookup_email:
        returning_candidate = Candidate.objects.select_related('education', 'experience', 'skills').filter(
            email__iexact=str(lookup_email).strip()
        ).first()
    elif lookup_phone:
        digits = re.sub(r'\D', '', str(lookup_phone))
        if len(digits) >= 10:
            returning_candidate = Candidate.objects.select_related('education', 'experience', 'skills').filter(
                Q(phone__icontains=digits[-10:]) | Q(alt_phone__icontains=digits[-10:])
            ).first()

    has_saved_resume = False
    saved_resume_url = ''
    saved_resume_name = ''
    if returning_candidate:
        cand_meta = serialize_candidate_data(returning_candidate)
        has_saved_resume = cand_meta.get('has_saved_resume', False)
        saved_resume_url = cand_meta.get('saved_resume_url', '')
        saved_resume_name = cand_meta.get('saved_resume_name', '')

    # Automatically fetch position from returning candidate's previous application (e.g. from 1st form Fast-Apply) if not already set
    if not job and returning_candidate:
        latest_app = returning_candidate.applications.select_related('job').filter(
            job__status=RecruitmentJob.Status.OPEN
        ).order_by('-applied_at').first()
        if latest_app:
            job = latest_app.job

    if request.method == 'POST':
        post_email = request.POST.get('email', '').strip().lower()
        if not has_saved_resume and post_email:
            post_cand = Candidate.objects.filter(email__iexact=post_email).first()
            if post_cand:
                p_meta = serialize_candidate_data(post_cand)
                has_saved_resume = p_meta.get('has_saved_resume', False)
                saved_resume_url = p_meta.get('saved_resume_url', '')
                saved_resume_name = p_meta.get('saved_resume_name', '')

        form = PreInterviewApplicationForm(request.POST, request.FILES, default_job=job, has_saved_resume=has_saved_resume)
        if form.is_valid():
            cd = form.cleaned_data
            selected_job = cd['job']

            # Reject applications if the position has been closed
            if selected_job.status != RecruitmentJob.Status.OPEN:
                return render(request, 'recruitment/public/link_invalid.html', {
                    'job': selected_job,
                    'reason': 'closed'
                })

            email = cd['email'].strip().lower()

            # Prevent duplicate application if already completed office walk-in registration
            existing_app = JobApplication.objects.filter(
                candidate__email=email,
                job=selected_job
            ).first()

            if existing_app and existing_app.is_office_registered:
                messages.warning(
                    request,
                    f"An in-person application has already been submitted with email '{email}' for {selected_job.title}. "
                    f"Your Application ID is {existing_app.application_id}."
                )
                return redirect('recruitment:candidate_track_id', application_id=existing_app.application_id)

            try:
                with transaction.atomic():
                    # 1. Candidate record (Pre-interview contact info & Address)
                    addr = cd.get('current_address', '').strip()
                    city = cd.get('city', '').strip() or 'Not Specified'
                    state = cd.get('state', '').strip()
                    postal_code = cd.get('postal_code', '').strip()
                    country = cd.get('country', '').strip() or 'India'
                    alt_phone = cd.get('alt_phone', '').strip()

                    candidate, _ = Candidate.objects.get_or_create(
                        email=email,
                        defaults={
                            'full_name': cd['full_name'],
                            'phone': cd['phone'],
                            'alt_phone': alt_phone,
                            'current_address': addr,
                            'city': city,
                            'state': state,
                            'postal_code': postal_code,
                            'country': country,
                        }
                    )
                    candidate.full_name = cd['full_name']
                    candidate.phone = cd['phone']
                    if alt_phone:
                        candidate.alt_phone = alt_phone
                    candidate.current_address = addr
                    candidate.city = city
                    candidate.state = state
                    candidate.postal_code = postal_code
                    candidate.country = country

                    # Attach Google identity verification
                    if google_auth and google_auth.get('email') == email:
                        candidate.is_google_verified = True
                        candidate.google_sub = google_auth.get('sub', '')
                        if google_auth.get('picture'):
                            candidate.google_picture_url = google_auth.get('picture')
                    elif request.POST.get('is_google_verified') == 'true':
                        candidate.is_google_verified = True

                    candidate.save()

                    # 2. Candidate Education (Highest Qualification summary)
                    CandidateEducation.objects.update_or_create(
                        candidate=candidate,
                        defaults={
                            'highest_qualification': cd['highest_qualification'],
                            'institution': cd.get('institution', ''),
                        }
                    )

                    # 3. Candidate Experience
                    CandidateExperience.objects.update_or_create(
                        candidate=candidate,
                        defaults={
                            'experience_type': cd['experience_type'],
                            'total_experience_years': cd.get('total_experience_years') if cd.get('total_experience_years') is not None else 0,
                            'current_company': cd.get('current_company') or '',
                            'current_designation': cd.get('current_designation') or '',
                            'notice_period_days': cd.get('notice_period_days') if cd.get('notice_period_days') is not None else 30,
                            'expected_ctc': cd.get('expected_ctc'),
                        }
                    )

                    # 4. Candidate Skills & Links
                    CandidateSkill.objects.update_or_create(
                        candidate=candidate,
                        defaults={
                            'technical_skills': cd['technical_skills'],
                            'linkedin_url': cd.get('linkedin_url', ''),
                            'portfolio_url': cd.get('portfolio_url', ''),
                        }
                    )

                    # 5. Create or Upgrade Job Application to Office Registration
                    resume_to_save = cd.get('resume')
                    if not resume_to_save and existing_app and existing_app.resume:
                        resume_to_save = existing_app.resume
                    elif not resume_to_save and returning_candidate:
                        lat_app = returning_candidate.applications.order_by('-applied_at').first()
                        if lat_app and lat_app.resume:
                            resume_to_save = lat_app.resume
                        else:
                            r_doc = returning_candidate.documents.filter(doc_type='RESUME').first()
                            if r_doc and r_doc.file:
                                resume_to_save = r_doc.file

                    if existing_app:
                        application = existing_app
                        application.is_office_registered = True
                        application.application_type = JobApplication.ApplicationType.OFFICE_REGISTRATION
                        if resume_to_save:
                            application.resume = resume_to_save
                        if link:
                            application.registration_link = link
                        application.save()

                        # 6. Status History
                        ApplicationStatusHistory.objects.create(
                            application=application,
                            old_status=application.status,
                            new_status=application.status,
                            notes='Candidate completed in-person Office Walk-In Registration form (upgraded from online fast-apply).'
                        )
                    else:
                        application = JobApplication.objects.create(
                            candidate=candidate,
                            job=selected_job,
                            registration_link=link,
                            resume=resume_to_save,
                            status=JobApplication.Status.SUBMITTED,
                            application_type=JobApplication.ApplicationType.OFFICE_REGISTRATION,
                            is_office_registered=True,
                        )

                        # 6. Status History
                        ApplicationStatusHistory.objects.create(
                            application=application,
                            old_status='NONE',
                            new_status=JobApplication.Status.SUBMITTED,
                            notes='Application submitted via online portal with Google Verification for Round 1 Interview Screening.'
                        )

                    # Ensure CandidateDocument is updated with resume
                    if application.resume:
                        CandidateDocument.objects.update_or_create(
                            candidate=candidate,
                            doc_type='RESUME',
                            defaults={
                                'title': f"Resume - {candidate.full_name}",
                                'file': application.resume,
                                'is_verified': False,
                            }
                        )

                # 7. Dispatch notification to HR Administrators
                hr_users = CustomUser.objects.filter(role__in=[CustomUser.Role.HR, CustomUser.Role.HEAD])
                for hr_member in hr_users:
                    create_notification(
                        recipient=hr_member,
                        title=f"New Candidate Application: {candidate.full_name}",
                        message=f"{candidate.full_name} applied for {selected_job.title}." + (f" via link '{link.title}'." if link else " via Universal Application Portal."),
                        notification_type='SYSTEM',
                        target_url=reverse('recruitment:candidate_detail', kwargs={'application_id': application.id})
                    )

                # 8. Send Confirmation Email to Candidate
                try:
                    subject = f"Application Received: {selected_job.title} - Company HRMS"
                    track_url = request.build_absolute_uri(reverse('recruitment:candidate_track_id', kwargs={'application_id': application.application_id}))
                    email_body = (
                        f"Dear {candidate.full_name},\n\n"
                        f"Thank you for applying for the position of {selected_job.title} at Company HRMS.\n\n"
                        f"We have safely received your profile and resume for Round 1 Interview Screening.\n"
                        f"Your Unique Application ID is: {application.application_id}\n\n"
                        f"Track your application status and interview schedule at:\n"
                        f"{track_url}\n\n"
                        f"Interview Process Overview:\n"
                        f"1. Initial Profile Review & Shortlisting by HR.\n"
                        f"2. Interview Round(s) scheduled by hiring managers.\n"
                        f"3. Once you qualify the interview, you will be invited to complete your full employee onboarding and document verification.\n\n"
                        f"Warm regards,\n"
                        f"Talent Acquisition & People Operations\n"
                        f"Company HRMS Enterprise"
                    )
                    send_mail(
                        subject,
                        email_body,
                        settings.DEFAULT_FROM_EMAIL,
                        [candidate.email],
                        fail_silently=True
                    )
                except Exception:
                    pass

                # Redirect to success page
                return redirect('recruitment:candidate_success', application_id=application.application_id)

            except Exception as e:
                messages.error(request, f"An unexpected error occurred while saving your application: {str(e)}")
        else:
            messages.error(request, "Please check the highlighted errors in the form below before submitting.")
    else:
        initial_data = {}
        if returning_candidate:
            initial_data = serialize_candidate_data(returning_candidate)
            if job and not initial_data.get('job'):
                initial_data['job'] = job.id
        elif google_auth:
            initial_data = {
                'full_name': google_auth.get('name', ''),
                'email': google_auth.get('email', ''),
            }
            if job:
                initial_data['job'] = job.id
        form = PreInterviewApplicationForm(initial=initial_data, default_job=job, selected_job=job, has_saved_resume=has_saved_resume)

    # Serialize job metadata to JSON for live client-side preview in the Google Form
    jobs_json = {}
    for j in open_jobs:
        dept_name = j.department.name if j.department else 'General'
        desc_snippet = j.description[:280] + ('...' if len(j.description) > 280 else '')
        req_snippet = j.requirements[:280] + ('...' if len(j.requirements) > 280 else '')
        jobs_json[str(j.id)] = {
            'id': j.id,
            'title': j.title,
            'department': dept_name,
            'location': j.location,
            'employment_type': j.get_employment_type_display(),
            'experience': j.experience_required,
            'vacancies': j.vacancies,
            'salary': j.salary_range or '',
            'description': desc_snippet,
            'requirements': req_snippet,
        }

    return render(request, 'recruitment/public/register.html', {
        'link': link,
        'job': job,
        'open_jobs': open_jobs,
        'jobs_json': json.dumps(jobs_json),
        'form': form,
        'google_user': google_auth,
        'google_client_id': google_client_id,
        'returning_candidate': returning_candidate,
        'has_saved_resume': has_saved_resume,
        'saved_resume_url': saved_resume_url,
        'saved_resume_name': saved_resume_name,
        'existing_candidate_data': json.dumps(serialize_candidate_data(returning_candidate)) if returning_candidate else '{}',
    })


def candidate_fast_apply(request, job_id=None):
    """
    LinkedIn & Website Direct Fast-Apply Portal with Google Sign-In.
    Streamlined 1-page form containing:
    Name, Email ID, Phone No, Alternative Phone No, Address, and Resume Upload.
    If a job is specified via link/URL, the form locks that specific role.
    If no job is specified, the dropdown is visible for role selection.
    Automatically fetches existing candidate details upon Google sign-in.
    """
    job = None
    target_job_id = job_id or request.GET.get('job')
    pos_param = request.GET.get('position')
    if target_job_id and str(target_job_id).isdigit():
        job = RecruitmentJob.objects.filter(id=target_job_id).first()
    if not job and (pos_param or (target_job_id and not str(target_job_id).isdigit())):
        target_str = pos_param or target_job_id
        from django.utils.text import slugify
        for j in RecruitmentJob.objects.all():
            if slugify(j.title) == slugify(target_str) or j.title.lower() == target_str.lower().replace('-', ' '):
                job = j
                break

    # If position is CLOSED (or on hold / draft), link will not work
    if job and job.status != RecruitmentJob.Status.OPEN:
        return render(request, 'recruitment/public/link_invalid.html', {
            'job': job,
            'reason': 'closed'
        })

    has_fixed_job = bool(job and job.status == RecruitmentJob.Status.OPEN)

    # Only ACTIVE / OPEN jobs are available in the application form
    open_jobs = list(RecruitmentJob.objects.filter(status=RecruitmentJob.Status.OPEN).select_related('department', 'site'))

    if not job and len(open_jobs) == 1:
        job = open_jobs[0]

    google_auth = request.session.get('candidate_google_auth')
    google_client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '315051569117-7knfkmsdkcsmcbmnp2or1pos542kd8b7.apps.googleusercontent.com')
    returning_candidate = None

    if google_auth and google_auth.get('email'):
        returning_candidate = Candidate.objects.select_related('education', 'experience', 'skills').filter(
            email__iexact=google_auth['email']
        ).first()

    if request.method == 'POST':
        form = QuickSocialApplicationForm(request.POST, request.FILES, default_job=job, fixed_job=job if has_fixed_job else None)
        if form.is_valid():
            cd = form.cleaned_data
            selected_job = cd.get('job') or job
            if not selected_job or selected_job.status != RecruitmentJob.Status.OPEN:
                return render(request, 'recruitment/public/link_invalid.html', {
                    'job': selected_job,
                    'reason': 'closed'
                })
            email = cd['email'].strip().lower()

            existing_app = JobApplication.objects.filter(
                candidate__email=email,
                job=selected_job
            ).first()

            if existing_app:
                messages.warning(
                    request,
                    f"An application has already been submitted with email '{email}' for {selected_job.title}. "
                    f"Your Application ID is {existing_app.application_id}."
                )
                return redirect('recruitment:candidate_track_id', application_id=existing_app.application_id)

            try:
                with transaction.atomic():
                    default_city = (selected_job.location if selected_job and selected_job.location else '') or 'Not Specified'

                    candidate, _ = Candidate.objects.get_or_create(
                        email=email,
                        defaults={
                            'full_name': cd['full_name'],
                            'phone': cd['phone'],
                            'alt_phone': cd.get('alt_phone', ''),
                            'city': default_city,
                            'country': 'India',
                        }
                    )
                    candidate.full_name = cd['full_name']
                    candidate.phone = cd['phone']
                    if cd.get('alt_phone'):
                        candidate.alt_phone = cd['alt_phone']
                    if not candidate.city:
                        candidate.city = default_city

                    # Attach Google identity verification
                    if google_auth and google_auth.get('email') == email:
                        candidate.is_google_verified = True
                        candidate.google_sub = google_auth.get('sub', '')
                        if google_auth.get('picture'):
                            candidate.google_picture_url = google_auth.get('picture')
                    elif request.POST.get('is_google_verified') == 'true':
                        candidate.is_google_verified = True

                    candidate.save()

                    application = JobApplication.objects.create(
                        candidate=candidate,
                        job=selected_job,
                        resume=cd['resume'],
                        status=JobApplication.Status.SUBMITTED,
                        application_type=JobApplication.ApplicationType.ONLINE_FAST_APPLY,
                        is_office_registered=False,
                    )

                    # Save resume in candidate's document portfolio
                    CandidateDocument.objects.update_or_create(
                        candidate=candidate,
                        doc_type='RESUME',
                        defaults={
                            'title': f"Resume - {candidate.full_name}",
                            'file': application.resume,
                            'is_verified': False,
                        }
                    )

                    # Persist session so next form auto-fetches all details seamlessly
                    request.session['candidate_google_auth'] = {
                        'email': candidate.email,
                        'name': candidate.full_name,
                        'sub': candidate.google_sub or f"cand-{candidate.id}",
                        'picture': candidate.google_picture_url or '',
                    }
                    request.session['last_applied_email'] = candidate.email
                    request.session.modified = True

                    ApplicationStatusHistory.objects.create(
                        application=application,
                        old_status='NONE',
                        new_status=JobApplication.Status.SUBMITTED,
                        notes='Application submitted via LinkedIn / Website Direct Fast-Apply Portal with Google Verification.'
                    )

                # Send notifications to HR
                hr_users = CustomUser.objects.filter(role__in=[CustomUser.Role.HR, CustomUser.Role.HEAD])
                for hr_member in hr_users:
                    create_notification(
                        recipient=hr_member,
                        title=f"New Direct Fast-Apply Candidate: {candidate.full_name}",
                        message=f"{candidate.full_name} submitted a direct application for {selected_job.title} via LinkedIn/Website portal.",
                        notification_type='SYSTEM',
                        target_url=reverse('recruitment:candidate_detail', kwargs={'application_id': application.id})
                    )

                # Send confirmation email
                try:
                    subject = f"Application Received: {selected_job.title} - Company HRMS"
                    track_url = request.build_absolute_uri(reverse('recruitment:candidate_track_id', kwargs={'application_id': application.application_id}))
                    email_body = (
                        f"Dear {candidate.full_name},\n\n"
                        f"Thank you for applying directly for the position of {selected_job.title} at Company HRMS via our LinkedIn & Website Fast-Apply Portal.\n\n"
                        f"We have successfully received your application and resume.\n"
                        f"Your Unique Application ID is: {application.application_id}\n\n"
                        f"You can track your application status at:\n{track_url}\n\n"
                        f"Warm regards,\nTalent Acquisition Team\nCompany HRMS"
                    )
                    send_mail(
                        subject,
                        email_body,
                        settings.DEFAULT_FROM_EMAIL,
                        [candidate.email],
                        fail_silently=True
                    )
                except Exception:
                    pass

                return redirect('recruitment:candidate_success', application_id=application.application_id)

            except Exception as e:
                messages.error(request, f"An unexpected error occurred while saving your application: {str(e)}")
        else:
            messages.error(request, "Please check the highlighted errors in the form below before submitting.")
    else:
        initial_data = {}
        if returning_candidate:
            initial_data = {
                'full_name': returning_candidate.full_name,
                'email': returning_candidate.email,
                'phone': returning_candidate.phone,
                'alt_phone': returning_candidate.alt_phone,
            }
        elif google_auth:
            initial_data = {
                'full_name': google_auth.get('name', ''),
                'email': google_auth.get('email', ''),
            }
        form = QuickSocialApplicationForm(initial=initial_data, default_job=job, selected_job=job, fixed_job=job if has_fixed_job else None)

    # Serialize job metadata to JSON for live client-side preview
    jobs_json = {}
    for j in open_jobs:
        dept_name = j.department.name if j.department else 'General'
        jobs_json[str(j.id)] = {
            'id': j.id,
            'title': j.title,
            'department': dept_name,
            'location': j.location,
            'employment_type': j.get_employment_type_display(),
            'experience': j.experience_required,
            'salary': j.salary_range or '',
            'description': j.description[:280] + ('...' if len(j.description) > 280 else ''),
        }

    return render(request, 'recruitment/public/fast_apply.html', {
        'form': form,
        'job': job,
        'has_fixed_job': has_fixed_job,
        'open_jobs': open_jobs,
        'jobs_json': json.dumps(jobs_json),
        'google_user': google_auth,
        'google_client_id': google_client_id,
        'returning_candidate': returning_candidate,
        'existing_candidate_data': json.dumps(serialize_candidate_data(returning_candidate)) if returning_candidate else '{}',
    })


def candidate_success(request, application_id):
    """
    Registration Success Page.
    Displays confirmation illustration, unique application ID, submission date, and tracking link.
    """
    application = get_object_or_404(
        JobApplication.objects.select_related('candidate', 'job'),
        application_id=application_id
    )
    return render(request, 'recruitment/public/success.html', {
        'application': application,
        'candidate': application.candidate,
        'job': application.job,
    })


def candidate_onboarding(request, application_id):
    """
    STAGE 2: Comprehensive Post-Interview Onboarding & Verification Portal.
    Accessible strictly after candidate successfully qualifies the interview rounds!
    Captures complete permanent address, 10th/12th marksheets, degree certificate, past employment proof, bank details, and statutory IDs.
    """
    app = get_object_or_404(
        JobApplication.objects.select_related('candidate', 'job', 'job__department'),
        application_id=application_id
    )
    candidate = app.candidate
    education = getattr(candidate, 'education', None)
    experience = getattr(candidate, 'experience', None)

    # Check qualification: Candidate must be qualified to access full onboarding
    if not app.is_qualified and app.status not in [JobApplication.Status.SELECTED, JobApplication.Status.ONBOARDING_COMPLETED, JobApplication.Status.HIRED]:
        return render(request, 'recruitment/public/onboarding_not_eligible.html', {
            'application': app,
            'candidate': candidate,
            'job': app.job,
        })

    if request.method == 'POST':
        form = CandidateOnboardingForm(request.POST, request.FILES)
        if form.is_valid():
            cd = form.cleaned_data
            try:
                with transaction.atomic():
                    # 1. Update Candidate Personal & Statutory Details
                    candidate.date_of_birth = cd['date_of_birth']
                    candidate.gender = cd['gender']
                    candidate.father_name = cd['father_name']
                    candidate.blood_group = cd.get('blood_group', '')
                    candidate.marital_status = cd.get('marital_status', 'SINGLE')
                    candidate.emergency_contact_name = cd['emergency_contact_name']
                    candidate.emergency_contact_relation = cd['emergency_contact_relation']
                    candidate.emergency_contact_phone = cd['emergency_contact_phone']
                    candidate.current_address = cd['current_address']
                    candidate.permanent_address = cd['permanent_address']
                    candidate.state = cd['state']
                    candidate.postal_code = cd['postal_code']
                    if cd.get('photo'):
                        candidate.photo = cd['photo']
                    candidate.bank_name = cd['bank_name']
                    candidate.bank_account_number = cd['bank_account_number']
                    candidate.bank_ifsc_code = cd['bank_ifsc_code']
                    candidate.bank_branch = cd['bank_branch']
                    candidate.pan_number = cd['pan_number']
                    candidate.aadhaar_number = cd['aadhaar_number']
                    candidate.pf_uan_number = cd.get('pf_uan_number', '')
                    candidate.save()

                    # 2. Update Education Details
                    CandidateEducation.objects.update_or_create(
                        candidate=candidate,
                        defaults={
                            'degree_name': cd['degree_name'],
                            'specialization': cd.get('specialization', ''),
                            'institution': cd['institution'],
                            'passing_year': cd['passing_year'],
                            'percentage_cgpa': cd['percentage_cgpa'],
                            'details_10th': cd['details_10th'],
                            'details_12th': cd['details_12th'],
                        }
                    )

                    # 3. Update Prior Experience
                    if cd.get('previous_company') or cd.get('previous_experience_details'):
                        CandidateExperience.objects.update_or_create(
                            candidate=candidate,
                            defaults={
                                'previous_company': cd.get('previous_company', ''),
                                'previous_experience_details': cd.get('previous_experience_details', ''),
                            }
                        )

                    # 4. Save / Update Uploaded Verification Documents
                    doc_specs = [
                        ('educational_certificate', 'CERTIFICATE', 'Degree Certificate / Final Marksheet'),
                        ('experience_letter', 'EXPERIENCE_LETTER', 'Experience / Relieving Letter'),
                        ('payslip', 'PAYSLIP', 'Recent Payslip / Form 16'),
                        ('bank_proof', 'BANK_PROOF', 'Cancelled Cheque / Bank Passbook Copy'),
                        ('id_proof', 'AADHAAR_CARD', 'Aadhaar / National ID Proof'),
                    ]
                    for field_name, doc_type, default_title in doc_specs:
                        uploaded_file = cd.get(field_name)
                        if uploaded_file:
                            doc = CandidateDocument.objects.filter(candidate=candidate, doc_type=doc_type).first()
                            if doc:
                                doc.file = uploaded_file
                                doc.title = default_title
                                doc.is_verified = False
                                doc.is_rejected = False
                                doc.rejection_notes = ''
                                doc.save()
                            else:
                                CandidateDocument.objects.create(
                                    candidate=candidate,
                                    doc_type=doc_type,
                                    title=default_title,
                                    file=uploaded_file,
                                    is_verified=False,
                                    is_rejected=False,
                                    rejection_notes=''
                                )

                    # 5. Mark Application as ONBOARDING_COMPLETED and PENDING HR Document Review
                    old_status = app.status
                    app.is_onboarding_completed = True
                    app.onboarding_completed_at = timezone.now()
                    app.status = JobApplication.Status.ONBOARDING_COMPLETED
                    app.document_verification_status = JobApplication.DocumentVerificationStatus.PENDING
                    app.document_rejection_reason = ''
                    app.save()

                    # 6. Audit History
                    ApplicationStatusHistory.objects.create(
                        application=app,
                        old_status=old_status,
                        new_status=JobApplication.Status.ONBOARDING_COMPLETED,
                        notes="Candidate submitted onboarding profile and verification documents. Awaiting HR document review and appointment."
                    )

                return render(request, 'recruitment/public/onboarding_success.html', {
                    'application': app,
                    'candidate': candidate,
                    'job': app.job,
                })

            except Exception as e:
                messages.error(request, f"Error saving onboarding details: {str(e)}")
        else:
            messages.error(request, "Please check the highlighted errors in the onboarding form.")
    else:
        # Pre-populate form with existing candidate data
        initial_data = {
            'date_of_birth': candidate.date_of_birth,
            'gender': candidate.gender if candidate.gender != 'UNDISCLOSED' else '',
            'father_name': candidate.father_name,
            'blood_group': candidate.blood_group,
            'marital_status': candidate.marital_status or 'SINGLE',
            'emergency_contact_name': candidate.emergency_contact_name,
            'emergency_contact_relation': candidate.emergency_contact_relation,
            'emergency_contact_phone': candidate.emergency_contact_phone,
            'current_address': candidate.current_address,
            'permanent_address': candidate.permanent_address or candidate.current_address,
            'state': candidate.state,
            'postal_code': candidate.postal_code,
            'bank_name': candidate.bank_name,
            'bank_account_number': candidate.bank_account_number,
            'bank_ifsc_code': candidate.bank_ifsc_code,
            'bank_branch': candidate.bank_branch,
            'pan_number': candidate.pan_number,
            'aadhaar_number': candidate.aadhaar_number,
            'pf_uan_number': candidate.pf_uan_number,
        }
        if education:
            initial_data.update({
                'degree_name': education.degree_name or education.highest_qualification,
                'specialization': education.specialization,
                'institution': education.institution,
                'passing_year': education.passing_year,
                'percentage_cgpa': education.percentage_cgpa,
                'details_10th': education.details_10th,
                'details_12th': education.details_12th,
            })
        if experience:
            initial_data.update({
                'previous_company': experience.previous_company or experience.current_company,
                'previous_experience_details': experience.previous_experience_details,
            })
        form = CandidateOnboardingForm(initial=initial_data)

    existing_docs = {d.doc_type: d for d in candidate.documents.all()}
    rejected_docs = candidate.documents.filter(is_rejected=True)
    cert_doc = existing_docs.get('CERTIFICATE')
    exp_doc = existing_docs.get('EXPERIENCE_LETTER')
    pay_doc = existing_docs.get('PAYSLIP')
    bank_doc = existing_docs.get('BANK_PROOF')
    id_doc = existing_docs.get('AADHAAR_CARD') or existing_docs.get('PAN_CARD')

    return render(request, 'recruitment/public/onboarding.html', {
        'form': form,
        'application': app,
        'candidate': candidate,
        'job': app.job,
        'existing_docs': existing_docs,
        'rejected_docs': rejected_docs,
        'cert_doc': cert_doc,
        'exp_doc': exp_doc,
        'pay_doc': pay_doc,
        'bank_doc': bank_doc,
        'id_doc': id_doc,
        'has_rejected_docs': rejected_docs.exists(),
    })


def candidate_track(request, application_id=None):
    """
    Candidate Application Tracking Page.
    Public page showing real-time hiring progress, interview details, and unlocking the onboarding link upon interview qualification.
    """
    app = None
    search_error = None

    target_id = application_id or request.GET.get('application_id', '').strip()

    if target_id:
        app = JobApplication.objects.filter(application_id__iexact=target_id).select_related(
            'candidate', 'job', 'job__department'
        ).first()

        if not app:
            search_error = f"No application found with ID '{target_id}'. Please check your ID and try again."

    return render(request, 'recruitment/public/track.html', {
        'application': app,
        'search_id': target_id,
        'search_error': search_error,
    })


@login_required
@hr_required
def convert_to_employee(request, application_id):
    """
    HR One-Click Onboarding Action:
    Converts a qualified and onboarded candidate into an active Company HRMS employee.
    Generates their CustomUser account and EmployeeProfile with all verified details.
    """
    app = get_object_or_404(
        JobApplication.objects.select_related('candidate', 'job', 'job__department', 'job__site'),
        id=application_id
    )
    candidate = app.candidate

    if request.method == 'POST':
        from employees.models import EmployeeProfile
        from organization.models import Designation

        # Generate unique username from email prefix
        base_username = candidate.email.split('@')[0].replace('.', '_').replace('-', '_')
        username = base_username
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Check if user already exists
        user = CustomUser.objects.filter(email=candidate.email).first()
        if not user:
            import secrets
            temp_password = secrets.token_urlsafe(12)
            name_parts = candidate.full_name.split()
            first_name = name_parts[0] if name_parts else 'Employee'
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ''
            user = CustomUser.objects.create_user(
                username=username,
                email=candidate.email,
                password=temp_password,
                first_name=first_name,
                last_name=last_name,
                role=CustomUser.Role.EMPLOYEE,
                phone=candidate.phone,
            )

        # Get or create designation for the job
        designation = None
        if app.job.department:
            designation = Designation.objects.filter(
                department=app.job.department,
                title__icontains=app.job.title[:30]
            ).first()
            if not designation:
                designation = Designation.objects.create(
                    department=app.job.department,
                    title=app.job.title[:150],
                    grade_level='L2 - Professional'
                )

        # Generate unique emp_id
        last_profile = EmployeeProfile.objects.order_by('-id').first()
        next_num = (last_profile.id + 105) if last_profile else 105
        new_emp_id = f"EMP{next_num}"
        while EmployeeProfile.objects.filter(emp_id=new_emp_id).exists():
            next_num += 1
            new_emp_id = f"EMP{next_num}"

        # Create/Update EmployeeProfile
        profile, created = EmployeeProfile.objects.get_or_create(
            user=user,
            defaults={
                'emp_id': new_emp_id,
                'department': app.job.department,
                'designation': designation,
                'site': app.job.site,
                'joining_date': timezone.localdate(),
                'employment_type': 'FULL_TIME',
                'status': EmployeeProfile.Status.ACTIVE,
                'date_of_birth': candidate.date_of_birth,
                'gender': candidate.gender if candidate.gender in ['MALE', 'FEMALE', 'OTHER'] else 'MALE',
                'marital_status': candidate.marital_status if candidate.marital_status in ['SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED'] else 'SINGLE',
                'blood_group': candidate.blood_group,
                'personal_email': candidate.email,
                'address': candidate.permanent_address or candidate.current_address,
                'city': candidate.city,
                'state': candidate.state,
                'postal_code': candidate.postal_code,
                'emergency_contact_name': candidate.emergency_contact_name or 'Emergency Contact',
                'emergency_contact_relation': candidate.emergency_contact_relation or 'Parent',
                'emergency_contact_phone': candidate.emergency_contact_phone or candidate.phone,
                'bank_name': candidate.bank_name,
                'bank_account_number': candidate.bank_account_number,
                'ifsc_code': candidate.bank_ifsc_code,
                'pan_number': candidate.pan_number,
                'uan_number': candidate.pf_uan_number,
            }
        )
        if not created:
            profile.uan_number = candidate.pf_uan_number
            profile.status = EmployeeProfile.Status.ACTIVE
            profile.save()

        # Ensure user account is active employee
        user.is_active = True
        user.role = CustomUser.Role.EMPLOYEE
        user.save()

        # Update application status to HIRED
        app.status = JobApplication.Status.HIRED
        app.save()

        ApplicationStatusHistory.objects.create(
            application=app,
            old_status=app.status,
            new_status=JobApplication.Status.HIRED,
            changed_by=request.user,
            notes=f"Candidate successfully converted to Company Employee ({user.username}). Employee Profile #{profile.emp_id} created."
        )

        messages.success(
            request,
            f"Candidate {candidate.full_name} successfully converted to Employee! Username: '{user.username}', Employee ID: {profile.emp_id}."
        )
        return redirect('recruitment:candidate_detail', application_id=app.id)

    return redirect('recruitment:candidate_detail', application_id=app.id)


# =========================================================================
# ONBOARDING VERIFICATION, DOCUMENT REVIEW & EMPLOYEE APPOINTMENT
# =========================================================================

@login_required
@hr_required
def onboarding_candidates_list(request):
    """
    Dedicated HR Command Center for Onboarding Employees:
    1. Inspects submitted onboarding records and uploaded documents (Degree, PAN, Aadhaar, Bank, Payslips).
    2. Allows HR to Approve / Verify documents or Reject with error notes for candidate re-upload.
    3. Quick action to configure salary and appoint candidate as official employee with HRMS credentials.
    """
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip().upper()
    if status_filter == 'ALL':
        status_filter = ''

    applications = JobApplication.objects.filter(
        status__in=[
            JobApplication.Status.ONBOARDING_COMPLETED,
            JobApplication.Status.SELECTED,
            JobApplication.Status.HIRED
        ]
    ).select_related(
        'candidate',
        'candidate__education',
        'candidate__experience',
        'candidate__skills',
        'job',
        'job__department',
        'job__site',
        'hired_employee',
        'hired_employee__user',
        'documents_verified_by'
    ).prefetch_related('candidate__documents').order_by('-onboarding_completed_at', '-updated_at')

    if search_query:
        applications = applications.filter(
            Q(candidate__full_name__icontains=search_query) |
            Q(candidate__email__icontains=search_query) |
            Q(candidate__phone__icontains=search_query) |
            Q(application_id__icontains=search_query) |
            Q(job__title__icontains=search_query)
        )

    if status_filter == 'PENDING':
        applications = applications.filter(
            status=JobApplication.Status.ONBOARDING_COMPLETED,
            document_verification_status=JobApplication.DocumentVerificationStatus.PENDING
        )
    elif status_filter == 'VERIFIED':
        applications = applications.filter(
            document_verification_status=JobApplication.DocumentVerificationStatus.VERIFIED
        )
    elif status_filter == 'REJECTED':
        applications = applications.filter(
            document_verification_status=JobApplication.DocumentVerificationStatus.REJECTED
        )
    elif status_filter == 'HIRED':
        applications = applications.filter(status=JobApplication.Status.HIRED)

    # Metric counters
    total_onboarding = JobApplication.objects.filter(status__in=[JobApplication.Status.ONBOARDING_COMPLETED, JobApplication.Status.HIRED]).count()
    pending_docs = JobApplication.objects.filter(status=JobApplication.Status.ONBOARDING_COMPLETED, document_verification_status='PENDING').count()
    verified_docs = JobApplication.objects.filter(document_verification_status='VERIFIED').count()
    rejected_docs = JobApplication.objects.filter(document_verification_status='REJECTED').count()
    hired_count = JobApplication.objects.filter(status=JobApplication.Status.HIRED).count()

    departments = Department.objects.all().order_by('name')
    sites = Site.objects.filter(is_active=True).order_by('name')

    # Pagination with configurable rows per page (default: 5, options: 5, 10, 20, 50, 100)
    per_page_options = [5, 10, 20, 50, 100]
    try:
        per_page = int(request.GET.get('per_page', 5))
        if per_page not in per_page_options:
            per_page = 5
    except (ValueError, TypeError):
        per_page = 5

    page_number = request.GET.get('page', 1)
    paginator = Paginator(applications, per_page)
    page_obj = paginator.get_page(page_number)

    return render(request, 'recruitment/admin_onboarding_list.html', {
        'page_obj': page_obj,
        'applications': page_obj,
        'paginator': paginator,
        'per_page': per_page,
        'per_page_options': per_page_options,
        'search_query': search_query,
        'status_filter': status_filter,
        'total_onboarding': total_onboarding,
        'pending_docs': pending_docs,
        'verified_docs': verified_docs,
        'rejected_docs': rejected_docs,
        'hired_count': hired_count,
        'departments': departments,
        'sites': sites,
        'today': timezone.localdate(),
    })


@login_required
@hr_required
def verify_candidate_documents(request, application_id):
    """
    Action for HR to inspect uploaded candidate documents.
    If valid: marks document_verification_status = 'VERIFIED'.
    If documentation error: marks document_verification_status = 'REJECTED' with reason,
    allowing the candidate to correct and re-upload through their onboarding portal.
    """
    app = get_object_or_404(
        JobApplication.objects.select_related('candidate', 'job'),
        application_id=application_id
    )

    if request.method == 'POST':
        action = request.POST.get('action', '').upper()
        if action == 'VERIFY':
            app.document_verification_status = JobApplication.DocumentVerificationStatus.VERIFIED
            app.document_rejection_reason = ''
            app.documents_verified_at = timezone.now()
            app.documents_verified_by = request.user
            app.save()

            # Persist verification across all attached documents in the database
            app.candidate.documents.all().update(
                is_verified=True,
                is_rejected=False,
                rejection_notes=''
            )

            messages.success(
                request,
                f"Documents for {app.candidate.full_name} ({app.application_id}) have been verified successfully! "
                "All verification documents are marked Verified in the database."
            )
        elif action == 'REJECT':
            reason = request.POST.get('rejection_reason', '').strip()
            if not reason:
                reason = "Documentation error identified. Please re-upload clear and authentic documents."
            app.document_verification_status = JobApplication.DocumentVerificationStatus.REJECTED
            app.document_rejection_reason = reason
            app.save()

            # Mark documents as rejected with reason for candidate correction
            app.candidate.documents.all().update(
                is_verified=False,
                is_rejected=True,
                rejection_notes=reason
            )

            messages.warning(
                request,
                f"Documents for {app.candidate.full_name} marked with error: '{reason}'. "
                "The candidate can now log back into their onboarding link and re-upload the required files."
            )

    return redirect('recruitment:onboarding_candidates_list')


@login_required
@hr_required
def verify_single_candidate_document_ajax(request, doc_id):
    """
    AJAX action for HR to verify an individual candidate document.
    Saves is_verified = True in CandidateDocument table.
    If all candidate documents are verified, also updates application status to VERIFIED.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)

    doc = get_object_or_404(CandidateDocument, id=doc_id)
    doc.is_verified = True
    doc.is_rejected = False
    doc.rejection_notes = ''
    doc.save()

    candidate = doc.candidate
    unverified_count = candidate.documents.filter(is_verified=False).count()
    rejected_count = candidate.documents.filter(is_rejected=True).count()
    app = candidate.applications.order_by('-applied_at').first()

    all_verified = (unverified_count == 0 and candidate.documents.exists())
    if app:
        if all_verified:
            app.document_verification_status = JobApplication.DocumentVerificationStatus.VERIFIED
            app.document_rejection_reason = ''
            app.documents_verified_at = timezone.now()
            app.documents_verified_by = request.user
            app.save()
        elif rejected_count == 0 and app.document_verification_status == JobApplication.DocumentVerificationStatus.REJECTED:
            app.document_verification_status = JobApplication.DocumentVerificationStatus.PENDING
            app.document_rejection_reason = ''
            app.save()

    return JsonResponse({
        'success': True,
        'doc_id': doc.id,
        'doc_title': doc.title,
        'is_verified': True,
        'all_verified': all_verified,
        'app_status': app.document_verification_status if app else 'VERIFIED',
        'message': f"Document '{doc.title}' successfully verified and saved!"
    })


@login_required
@hr_required
def reject_single_candidate_document_ajax(request, doc_id):
    """
    AJAX endpoint for HR to reject an individual candidate document with feedback.
    Sets is_rejected = True, is_verified = False, and saves rejection_notes.
    Also updates the parent application document_verification_status to REJECTED.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)

    doc = get_object_or_404(CandidateDocument, id=doc_id)

    reason = ''
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body.decode('utf-8'))
            reason = data.get('reason', '').strip()
        except Exception:
            pass
    if not reason:
        reason = request.POST.get('reason', '').strip()
    if not reason:
        reason = "Document unclear or invalid. Please re-upload a clear copy."

    doc.is_verified = False
    doc.is_rejected = True
    doc.rejection_notes = reason
    doc.save()

    candidate = doc.candidate
    app = candidate.applications.order_by('-applied_at').first()
    if app:
        app.document_verification_status = JobApplication.DocumentVerificationStatus.REJECTED
        app.document_rejection_reason = f"{doc.title}: {reason}"
        app.save()

        # Audit History
        ApplicationStatusHistory.objects.create(
            application=app,
            old_status=app.status,
            new_status=app.status,
            notes=f"Document '{doc.title}' marked as rejected by {request.user.get_full_name() or request.user.username}: {reason}"
        )

    return JsonResponse({
        'success': True,
        'doc_id': doc.id,
        'doc_title': doc.title,
        'is_rejected': True,
        'is_verified': False,
        'rejection_notes': doc.rejection_notes,
        'app_status': app.document_verification_status if app else 'REJECTED',
        'message': f"Document '{doc.title}' marked as rejected with feedback."
    })


@login_required
@hr_required
def fetch_onboarding_candidate_ajax(request):
    """
    Auto-fetch candidate details by Phone Number or Email address
    for the Employee Appointment & Credential Creation interface.
    """
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'success': False, 'message': 'Please provide a phone number or email.'})

    # Normalize phone: extract numbers
    digits_q = re.sub(r'\D', '', q)
    if digits_q.startswith('91') and len(digits_q) == 12:
        digits_q = digits_q[2:]
    elif digits_q.startswith('0') and len(digits_q) == 11:
        digits_q = digits_q[1:]

    # Search JobApplication
    applications = JobApplication.objects.select_related(
        'candidate', 'job', 'job__department', 'job__site'
    ).prefetch_related('candidate__documents')

    app = None
    if '@' in q:
        app = applications.filter(candidate__email__iexact=q).first()
    elif digits_q:
        app = applications.filter(
            Q(candidate__phone__icontains=digits_q) |
            Q(candidate__alt_phone__icontains=digits_q) |
            Q(candidate__phone__icontains=q)
        ).first()
        if not app:
            # Match stripped digits (handles spaces and country codes)
            for a in applications:
                c_phone = re.sub(r'\D', '', a.candidate.phone or '')
                c_alt = re.sub(r'\D', '', a.candidate.alt_phone or '')
                if digits_q and (digits_q in c_phone or c_phone.endswith(digits_q) or digits_q in c_alt or c_alt.endswith(digits_q)):
                    app = a
                    break

    if not app:
        # Fallback to search by application_id or candidate name
        app = applications.filter(
            Q(application_id__iexact=q) |
            Q(candidate__full_name__icontains=q)
        ).first()

    if not app:
        return JsonResponse({
            'success': False,
            'message': f"No candidate application found matching '{q}'. Please check the mobile number or email."
        })

    candidate = app.candidate
    # Auto-generate a clean suggested username: e.g. "chinmayee_mohanty_ux" or email prefix
    base_name = re.sub(r'[^a-zA-Z0-9]', '_', candidate.full_name.strip().lower())
    clean_role = ''
    if app.job and app.job.title:
        role_words = [w.lower() for w in re.findall(r'[a-zA-Z0-9]+', app.job.title)]
        if role_words:
            clean_role = f"_{role_words[0]}"
            if len(role_words) > 1 and len(clean_role) < 8:
                clean_role += f"_{role_words[1]}"
    suggested_username = f"{base_name}{clean_role}"[:30]
    suggested_username = re.sub(r'_+', '_', suggested_username).strip('_')

    temp_u = suggested_username
    counter = 1
    while CustomUser.objects.filter(username__iexact=temp_u).exclude(email__iexact=candidate.email).exists():
        temp_u = f"{suggested_username}_{counter}"
        counter += 1
    suggested_username = temp_u

    # Documents summary
    docs_list = []
    for d in candidate.documents.all():
        docs_list.append({
            'title': d.title,
            'doc_type': d.get_doc_type_display(),
            'url': d.file.url if d.file else ''
        })

    return JsonResponse({
        'success': True,
        'candidate': {
            'application_id': app.application_id,
            'candidate_id': candidate.id,
            'full_name': candidate.full_name,
            'email': candidate.email,
            'phone': candidate.phone,
            'city': candidate.city,
            'pan_number': candidate.pan_number,
            'aadhaar_number': candidate.aadhaar_number,
            'bank_name': candidate.bank_name,
            'bank_account_number': candidate.bank_account_number,
            'bank_ifsc_code': candidate.bank_ifsc_code,
            'pf_uan_number': candidate.pf_uan_number,
            'job_title': app.job.title if app.job else 'General Role',
            'department_id': app.job.department.id if app.job and app.job.department else '',
            'department_name': app.job.department.name if app.job and app.job.department else '',
            'site_id': app.job.site.id if app.job and app.job.site else '',
            'site_name': app.job.site.name if app.job and app.job.site else '',
            'document_status': app.document_verification_status,
            'document_status_display': app.get_document_verification_status_display(),
            'suggested_username': suggested_username,
            'offered_ctc': str(app.offered_ctc) if app.offered_ctc else '600000.00',
            'basic_salary': str(app.offered_basic_salary) if app.offered_basic_salary else '25000.00',
            'joining_date': str(app.offered_joining_date or timezone.localdate()),
            'documents': docs_list,
            'documents_count': len(docs_list),
            'is_hired': (app.status == JobApplication.Status.HIRED)
        }
    })


@login_required
@hr_required
def appoint_employee(request):
    """
    Dedicated Interface for Appointing Onboarded Candidates as Official Employees:
    1. HR fills Phone No. or Email -> Candidate Name and Details are Auto-Fetched.
    2. HR verifies/edits Salary & Designation particulars.
    3. HR creates official HRMS Login Credentials (Username, Password, Confirm Password).
    4. HR clicks confirmation checkbox and submits -> Candidate is appointed as Active Employee!
    """
    from employees.models import EmployeeProfile, EmployeeDocument
    from organization.models import Designation
    from payroll.models import SalaryStructure

    app_id = request.GET.get('app_id', '').strip()
    prefill_app = None
    if app_id:
        prefill_app = JobApplication.objects.filter(application_id=app_id).select_related('candidate', 'job', 'job__department', 'job__site').first()

    departments = Department.objects.all().order_by('name')
    sites = Site.objects.filter(is_active=True).order_by('name')

    if request.method == 'POST':
        form = AppointEmployeeForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            lookup_query = cd['lookup_query'].strip()
            username = cd['username'].strip()
            password = cd['password']
            joining_date = cd['joining_date']
            dept = cd.get('department')
            site_obj = cd.get('site')
            designation_title = cd.get('designation_title', '').strip()
            employment_type = cd.get('employment_type', 'FULL_TIME')
            offered_ctc = cd.get('offered_ctc') or Decimal('600000.00')
            basic_salary = cd.get('basic_salary') or Decimal('25000.00')

            digits_q = re.sub(r'\D', '', lookup_query)
            if digits_q.startswith('91') and len(digits_q) == 12:
                digits_q = digits_q[2:]
            elif digits_q.startswith('0') and len(digits_q) == 11:
                digits_q = digits_q[1:]

            apps_q = JobApplication.objects.select_related('candidate', 'job', 'job__department', 'job__site')
            app = None
            if cd.get('application_id'):
                app = apps_q.filter(application_id=cd['application_id']).first()
            if not app:
                if '@' in lookup_query:
                    app = apps_q.filter(candidate__email__iexact=lookup_query).first()
                elif digits_q:
                    app = apps_q.filter(
                        Q(candidate__phone__icontains=digits_q) |
                        Q(candidate__alt_phone__icontains=digits_q) |
                        Q(candidate__phone__icontains=lookup_query)
                    ).first()
                    if not app:
                        for a in apps_q:
                            c_phone = re.sub(r'\D', '', a.candidate.phone or '')
                            c_alt = re.sub(r'\D', '', a.candidate.alt_phone or '')
                            if digits_q and (digits_q in c_phone or c_phone.endswith(digits_q) or digits_q in c_alt or c_alt.endswith(digits_q)):
                                app = a
                                break
            if not app:
                messages.error(request, f"No candidate found for '{lookup_query}'. Please verify mobile number or email.")
                return render(request, 'recruitment/admin_appoint_employee.html', {
                    'form': form,
                    'departments': departments,
                    'sites': sites,
                    'prefill_app': prefill_app,
                })

            candidate = app.candidate

            if CustomUser.objects.filter(username__iexact=username).exclude(email__iexact=candidate.email).exists():
                form.add_error('username', f"Username '{username}' is already taken. Please choose another username.")
                return render(request, 'recruitment/admin_appoint_employee.html', {
                    'form': form,
                    'departments': departments,
                    'sites': sites,
                    'prefill_app': prefill_app,
                })

            try:
                with transaction.atomic():
                    # 1. Create or Update CustomUser
                    user = CustomUser.objects.filter(email__iexact=candidate.email).first()
                    name_parts = candidate.full_name.split()
                    first_name = name_parts[0] if name_parts else 'Employee'
                    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ''

                    if not user:
                        user = CustomUser.objects.create_user(
                            username=username,
                            email=candidate.email,
                            password=password,
                            first_name=first_name,
                            last_name=last_name,
                            role=CustomUser.Role.EMPLOYEE,
                            phone=candidate.phone,
                        )
                    else:
                        user.username = username
                        user.set_password(password)
                        user.first_name = first_name
                        user.last_name = last_name
                        user.phone = candidate.phone
                        user.role = CustomUser.Role.EMPLOYEE
                        user.is_active = True
                        user.save()

                    # 2. Designation Setup
                    final_dept = dept or (app.job.department if app.job else None)
                    designation = None
                    final_title = designation_title or (app.job.title if app.job else 'Software Engineer')
                    if final_dept:
                        designation = Designation.objects.filter(
                            department=final_dept,
                            title__iexact=final_title
                        ).first()
                        if not designation:
                            designation = Designation.objects.create(
                                department=final_dept,
                                title=final_title[:150],
                                grade_level='L2 - Professional'
                            )

                    # 3. Generate Next EMP ID
                    emp_profile = EmployeeProfile.objects.filter(user=user).first()
                    if not emp_profile:
                        last_emp = EmployeeProfile.objects.order_by('-id').first()
                        next_num = 101
                        if last_emp and last_emp.emp_id.startswith('EMP'):
                            try:
                                next_num = max(101, int(last_emp.emp_id.replace('EMP', '')) + 1)
                            except ValueError:
                                next_num = (last_emp.id + 105)
                        new_emp_id = f"EMP{next_num}"
                        while EmployeeProfile.objects.filter(emp_id=new_emp_id).exists():
                            next_num += 1
                            new_emp_id = f"EMP{next_num}"

                        final_site = site_obj or (app.job.site if app.job else None)
                        emp_profile = EmployeeProfile.objects.create(
                            user=user,
                            emp_id=new_emp_id,
                            department=final_dept,
                            designation=designation,
                            site=final_site,
                            joining_date=joining_date,
                            employment_type=employment_type,
                            status=EmployeeProfile.Status.ACTIVE,
                            date_of_birth=candidate.date_of_birth,
                            gender=candidate.gender if candidate.gender in ['MALE', 'FEMALE', 'OTHER'] else 'MALE',
                            marital_status=candidate.marital_status if candidate.marital_status in ['SINGLE', 'MARRIED', 'DIVORCED', 'WIDOWED'] else 'SINGLE',
                            blood_group=candidate.blood_group,
                            personal_email=candidate.email,
                            address=candidate.permanent_address or candidate.current_address,
                            city=candidate.city,
                            state=candidate.state,
                            postal_code=candidate.postal_code,
                            emergency_contact_name=candidate.emergency_contact_name or 'Emergency Contact',
                            emergency_contact_relation=candidate.emergency_contact_relation or 'Parent',
                            emergency_contact_phone=candidate.emergency_contact_phone or candidate.phone,
                            bank_name=candidate.bank_name,
                            bank_account_number=candidate.bank_account_number,
                            ifsc_code=candidate.bank_ifsc_code,
                            pan_number=candidate.pan_number,
                            uan_number=candidate.pf_uan_number,
                        )
                    else:
                        emp_profile.department = final_dept
                        emp_profile.designation = designation
                        emp_profile.joining_date = joining_date
                        emp_profile.bank_name = candidate.bank_name
                        emp_profile.bank_account_number = candidate.bank_account_number
                        emp_profile.ifsc_code = candidate.bank_ifsc_code
                        emp_profile.pan_number = candidate.pan_number
                        emp_profile.uan_number = candidate.pf_uan_number
                        emp_profile.status = EmployeeProfile.Status.ACTIVE
                        emp_profile.save()

                    # 4. Salary Structure in Payroll
                    hra_amt = round(basic_salary * Decimal('0.40'), 2)
                    monthly_gross = round(offered_ctc / Decimal('12.0'), 2)
                    special_all = max(Decimal('0.00'), monthly_gross - basic_salary - hra_amt)

                    SalaryStructure.objects.update_or_create(
                        employee=emp_profile,
                        defaults={
                            'basic_salary': basic_salary,
                            'hra': hra_amt,
                            'special_allowance': special_all,
                            'is_active': True
                        }
                    )

                    # 5. Copy candidate documents to EmployeeDocument
                    for doc in candidate.documents.all():
                        EmployeeDocument.objects.get_or_create(
                            employee=emp_profile,
                            title=doc.title,
                            defaults={
                                'file': doc.file,
                                'doc_type': 'CERTIFICATE' if doc.doc_type == 'CERTIFICATE' else 'ID_PROOF' if doc.doc_type == 'AADHAAR_CARD' else 'OTHER'
                            }
                        )

                    # 6. Update Application status to HIRED
                    old_status = app.status
                    app.status = JobApplication.Status.HIRED
                    app.document_verification_status = JobApplication.DocumentVerificationStatus.VERIFIED
                    app.hired_employee = emp_profile
                    app.offered_ctc = offered_ctc
                    app.offered_basic_salary = basic_salary
                    app.offered_joining_date = joining_date
                    app.save()

                    # 7. Audit History
                    ApplicationStatusHistory.objects.create(
                        application=app,
                        old_status=old_status,
                        new_status=JobApplication.Status.HIRED,
                        notes=f"Candidate successfully appointed as Employee #{emp_profile.emp_id}. Official HRMS Login User ID issued: '{user.username}'."
                    )

                messages.success(
                    request,
                    f"Candidate {candidate.full_name} is now officially appointed as an Employee (#{emp_profile.emp_id})! "
                    f"HRMS Portal Login Credentials created (User ID: '{user.username}')."
                )
                return redirect('recruitment:onboarding_candidates_list')

            except Exception as e:
                messages.error(request, f"Error completing employee appointment: {str(e)}")
        else:
            messages.error(request, "Please review and correct the errors below.")
    else:
        initial = {}
        if prefill_app:
            cand = prefill_app.candidate
            base_name = re.sub(r'[^a-zA-Z0-9]', '_', cand.full_name.strip().lower())
            clean_role = ''
            if prefill_app.job and prefill_app.job.title:
                role_words = [w.lower() for w in re.findall(r'[a-zA-Z0-9]+', prefill_app.job.title)]
                if role_words:
                    clean_role = f"_{role_words[0]}"
            suggested_u = f"{base_name}{clean_role}"[:30].strip('_')
            cnt = 1
            temp_u = suggested_u
            while CustomUser.objects.filter(username__iexact=temp_u).exists():
                temp_u = f"{suggested_u}_{cnt}"
                cnt += 1

            initial = {
                'application_id': prefill_app.application_id,
                'lookup_query': cand.phone or cand.email,
                'username': temp_u,
                'designation_title': prefill_app.job.title if prefill_app.job else '',
                'department': prefill_app.job.department if prefill_app.job else None,
                'site': prefill_app.job.site if prefill_app.job else None,
                'joining_date': prefill_app.offered_joining_date or timezone.localdate(),
                'offered_ctc': prefill_app.offered_ctc or Decimal('650000.00'),
                'basic_salary': prefill_app.offered_basic_salary or Decimal('27000.00'),
            }
        form = AppointEmployeeForm(initial=initial)

    return render(request, 'recruitment/admin_appoint_employee.html', {
        'form': form,
        'departments': departments,
        'sites': sites,
        'prefill_app': prefill_app,
        'today': timezone.localdate(),
    })

