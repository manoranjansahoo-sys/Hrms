import os
import csv
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
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
    ScheduleInterviewForm
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
    universal_apply_url = f"{scheme}://{host}/candidate/apply/"
    fast_apply_url = f"{scheme}://{host}/candidate/fast-apply/"
    quick_job_form = JobOpeningForm()

    return render(request, 'recruitment/candidate_links_list.html', {
        'links': links,
        'jobs': jobs,
        'active_jobs_count': jobs.filter(status=RecruitmentJob.Status.OPEN).count(),
        'total_applications_count': JobApplication.objects.count(),
        'search_query': search_query,
        'status_filter': status_filter,
        'host_url': f"{scheme}://{host}",
        'universal_apply_url': universal_apply_url,
        'fast_apply_url': fast_apply_url,
        'quick_job_form': quick_job_form,
        'sites': Site.objects.filter(is_active=True).order_by('name'),
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
    """Manage company job openings."""
    jobs = RecruitmentJob.objects.select_related('department', 'site').annotate(
        app_count=Count('applications')
    ).all()
    return render(request, 'recruitment/jobs_list.html', {'jobs': jobs})


@login_required
@hr_required
def create_job_opening(request):
    """Create a new job opening."""
    if request.method == 'POST':
        form = JobOpeningForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.created_by = request.user
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
            if next_url:
                return redirect(next_url)
            return redirect('recruitment:jobs_list')
    else:
        form = JobOpeningForm()
    return render(request, 'recruitment/job_form.html', {'form': form, 'is_new': True})


@login_required
@hr_required
def edit_job_opening(request, job_id):
    """Edit existing job opening."""
    job = get_object_or_404(RecruitmentJob, id=job_id)
    next_url = request.POST.get('next') or request.GET.get('next') or ''
    if request.method == 'POST':
        form = JobOpeningForm(request.POST, instance=job)
        if form.is_valid():
            saved_job = form.save(commit=False)
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
            return redirect('recruitment:jobs_list')
    else:
        form = JobOpeningForm(instance=job)
    return render(request, 'recruitment/job_form.html', {
        'form': form,
        'job': job,
        'is_new': False,
        'next_url': next_url,
    })


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
    """
    applications = JobApplication.objects.select_related(
        'candidate', 'candidate__experience', 'candidate__education',
        'candidate__skills', 'job', 'job__department'
    ).all()

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

    # Summary metrics
    total_apps = JobApplication.objects.count()
    under_review = JobApplication.objects.filter(status=JobApplication.Status.UNDER_REVIEW).count()
    shortlisted = JobApplication.objects.filter(status=JobApplication.Status.SHORTLISTED).count()
    interview_scheduled = JobApplication.objects.filter(status=JobApplication.Status.INTERVIEW_SCHEDULED).count()
    selected = JobApplication.objects.filter(status=JobApplication.Status.SELECTED).count()
    hired = JobApplication.objects.filter(status=JobApplication.Status.HIRED).count()

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
    universal_apply_url = f"{scheme}://{host}/candidate/apply/"

    return render(request, 'recruitment/candidates_list.html', {
        'page_obj': page_obj,
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
    })


@login_required
@hr_required
def export_candidates_csv(request):
    """
    Export candidate applications pipeline to a CSV spreadsheet report.
    Respects current filters and search query parameters.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="Candidate_Pipeline_{timezone.now().strftime("%Y%m%d_%H%M")}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Application ID', 'Candidate Name', 'Email', 'Phone',
        'Job Role', 'Department', 'Location',
        'Experience Type', 'Total Experience', 'Current Company',
        'Highest Qualification', 'Institution', 'Status',
        'Applied Date'
    ])

    applications = JobApplication.objects.select_related(
        'candidate', 'candidate__education', 'candidate__experience',
        'job', 'job__department'
    ).all()

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
                        f"{request.scheme}://{request.get_host()}/candidate/track/{app.application_id}/\n\n"
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
# 2. PUBLIC CANDIDATE REGISTRATION VIEWS (No Authentication Required!)
# =========================================================================

def candidate_register(request, token=None):
    """
    STAGE 1: Public Pre-Interview Candidate Registration (Google Form Style).
    Supports:
    1. Universal / Master link: /candidate/apply/ or /candidate/register/ (token=None)
       Candidate selects any active position from master data.
    2. Specific campaign link: /candidate/register/<token>/
       Pre-selects link.job and associates application with the link.
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
        # Check query param for preselecting job (e.g. ?job=1)
        job_id_param = request.GET.get('job')
        if job_id_param:
            job = RecruitmentJob.objects.filter(id=job_id_param).first()

    open_jobs = list(RecruitmentJob.objects.filter(status=RecruitmentJob.Status.OPEN).select_related('department', 'site'))

    # If previewing a specific job that is not in open_jobs, include it for preview display
    if job and job not in open_jobs:
        open_jobs.insert(0, job)

    if not job and len(open_jobs) == 1:
        job = open_jobs[0]

    if request.method == 'POST':
        form = PreInterviewApplicationForm(request.POST, request.FILES, default_job=job)
        if form.is_valid():
            cd = form.cleaned_data
            selected_job = cd['job']
            email = cd['email'].strip().lower()

            # Prevent duplicate application for the same job with the same email
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
                    # 1. Candidate record (Pre-interview contact info)
                    candidate, _ = Candidate.objects.get_or_create(
                        email=email,
                        defaults={
                            'full_name': cd['full_name'],
                            'phone': cd['phone'],
                            'city': cd['city'],
                            'country': 'India',
                        }
                    )
                    candidate.full_name = cd['full_name']
                    candidate.phone = cd['phone']
                    candidate.city = cd['city']
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
                            'total_experience_years': cd.get('total_experience_years', 0),
                            'current_company': cd.get('current_company', ''),
                            'current_designation': cd.get('current_designation', ''),
                            'notice_period_days': cd.get('notice_period_days', 30),
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

                    # 5. Create Job Application
                    application = JobApplication.objects.create(
                        candidate=candidate,
                        job=selected_job,
                        registration_link=link,
                        resume=cd['resume'],
                        status=JobApplication.Status.SUBMITTED
                    )

                    # 6. Status History
                    ApplicationStatusHistory.objects.create(
                        application=application,
                        old_status='NONE',
                        new_status=JobApplication.Status.SUBMITTED,
                        notes='Application submitted via online portal for Round 1 Interview Screening.'
                    )

                # 7. Dispatch notification to HR Administrators
                hr_users = CustomUser.objects.filter(role__in=[CustomUser.Role.HR, CustomUser.Role.HEAD])
                for hr_member in hr_users:
                    create_notification(
                        recipient=hr_member,
                        title=f"New Candidate Application: {candidate.full_name}",
                        message=f"{candidate.full_name} applied for {selected_job.title}." + (f" via link '{link.title}'." if link else " via Universal Application Portal."),
                        notification_type='SYSTEM',
                        target_url=f"/hr/candidates/{application.id}/"
                    )

                # 8. Send Confirmation Email to Candidate
                try:
                    subject = f"Application Received: {selected_job.title} - Company HRMS"
                    track_url = f"{request.scheme}://{request.get_host()}/candidate/track/{application.application_id}/"
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
        form = PreInterviewApplicationForm(default_job=job, selected_job=job)

    # Serialize job metadata to JSON for live client-side preview in the Google Form
    import json
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
    })


def candidate_fast_apply(request, job_id=None):
    """
    LinkedIn & Website Direct Fast-Apply Portal with Google Sign-In.
    Streamlined 1-page form containing:
    Name, Email ID, Phone No, Alternative Phone No, Address, and Resume Upload.
    If a job is specified via link/URL, the form locks that specific role.
    If no job is specified, the dropdown is visible for role selection.
    """
    job = None
    target_job_id = job_id or request.GET.get('job')
    if target_job_id:
        job = RecruitmentJob.objects.filter(id=target_job_id).first()

    has_fixed_job = bool(job)

    open_jobs = list(RecruitmentJob.objects.filter(status=RecruitmentJob.Status.OPEN).select_related('department', 'site'))
    if job and job not in open_jobs:
        open_jobs.insert(0, job)
    if not job and len(open_jobs) == 1:
        job = open_jobs[0]

    if request.method == 'POST':
        form = QuickSocialApplicationForm(request.POST, request.FILES, default_job=job, fixed_job=job if has_fixed_job else None)
        if form.is_valid():
            cd = form.cleaned_data
            selected_job = cd.get('job') or job
            if not selected_job:
                messages.error(request, "Please select the position you are applying for.")
                return redirect(request.path)
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
                    addr = cd['current_address'].strip()
                    city = cd.get('city', '').strip() or 'Not Specified'
                    state = cd.get('state', '').strip()
                    postal_code = cd.get('postal_code', '').strip()
                    country = cd.get('country', '').strip() or 'India'

                    candidate, _ = Candidate.objects.get_or_create(
                        email=email,
                        defaults={
                            'full_name': cd['full_name'],
                            'phone': cd['phone'],
                            'alt_phone': cd.get('alt_phone', ''),
                            'current_address': addr,
                            'city': city,
                            'state': state,
                            'postal_code': postal_code,
                            'country': country,
                        }
                    )
                    candidate.full_name = cd['full_name']
                    candidate.phone = cd['phone']
                    candidate.alt_phone = cd.get('alt_phone', '')
                    candidate.current_address = addr
                    candidate.city = city
                    candidate.state = state
                    candidate.postal_code = postal_code
                    candidate.country = country
                    candidate.save()

                    application = JobApplication.objects.create(
                        candidate=candidate,
                        job=selected_job,
                        resume=cd['resume'],
                        status=JobApplication.Status.SUBMITTED
                    )

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
                        target_url=f"/hr/candidates/{application.id}/"
                    )

                # Send confirmation email
                try:
                    subject = f"Application Received: {selected_job.title} - Company HRMS"
                    track_url = f"{request.scheme}://{request.get_host()}/candidate/track/{application.application_id}/"
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
        form = QuickSocialApplicationForm(default_job=job, selected_job=job, fixed_job=job if has_fixed_job else None)

    # Serialize job metadata to JSON for live client-side preview
    import json
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

                    # 4. Save Uploaded Verification Documents
                    if cd.get('educational_certificate'):
                        CandidateDocument.objects.create(
                            candidate=candidate,
                            doc_type='CERTIFICATE',
                            title='Degree Certificate / Final Marksheet',
                            file=cd['educational_certificate']
                        )
                    if cd.get('experience_letter'):
                        CandidateDocument.objects.create(
                            candidate=candidate,
                            doc_type='EXPERIENCE_LETTER',
                            title='Experience / Relieving Letter',
                            file=cd['experience_letter']
                        )
                    if cd.get('payslip'):
                        CandidateDocument.objects.create(
                            candidate=candidate,
                            doc_type='PAYSLIP',
                            title='Recent Payslip',
                            file=cd['payslip']
                        )
                    if cd.get('bank_proof'):
                        CandidateDocument.objects.create(
                            candidate=candidate,
                            doc_type='BANK_PROOF',
                            title='Cancelled Cheque / Bank Passbook Copy',
                            file=cd['bank_proof']
                        )
                    if cd.get('id_proof'):
                        CandidateDocument.objects.create(
                            candidate=candidate,
                            doc_type='AADHAAR_CARD',
                            title='Aadhaar / National ID Proof',
                            file=cd['id_proof']
                        )

                    # 5. Create / Update Active CustomUser & EmployeeProfile
                    username = cd.get('username', '').strip()
                    if not username:
                        username = candidate.email.split('@')[0].replace('.', '_').replace('-', '_')

                    user = CustomUser.objects.filter(email__iexact=candidate.email).first()
                    if not user:
                        base_u = username
                        cnt = 1
                        while CustomUser.objects.filter(username__iexact=username).exists():
                            username = f"{base_u}{cnt}"
                            cnt += 1

                        name_parts = candidate.full_name.split()
                        first_name = name_parts[0] if name_parts else 'Employee'
                        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ''
                        user = CustomUser.objects.create_user(
                            username=username,
                            email=candidate.email,
                            password=cd['portal_password'],
                            first_name=first_name,
                            last_name=last_name,
                            role=CustomUser.Role.EMPLOYEE,
                            phone=candidate.phone,
                        )
                    else:
                        user.set_password(cd['portal_password'])
                        user.role = CustomUser.Role.EMPLOYEE
                        user.is_active = True
                        if not user.phone:
                            user.phone = candidate.phone
                        user.save()

                    # Create / link EmployeeProfile
                    from employees.models import EmployeeProfile, EmployeeDocument
                    from organization.models import Designation

                    designation = None
                    if app.job and app.job.department:
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

                    # Auto generate EMP ID
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

                        emp_profile = EmployeeProfile.objects.create(
                            user=user,
                            emp_id=new_emp_id,
                            department=app.job.department if app.job else None,
                            designation=designation,
                            site=app.job.site if app.job else None,
                            joining_date=timezone.localdate(),
                            employment_type='FULL_TIME',
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
                        emp_profile.bank_name = candidate.bank_name
                        emp_profile.bank_account_number = candidate.bank_account_number
                        emp_profile.ifsc_code = candidate.bank_ifsc_code
                        emp_profile.pan_number = candidate.pan_number
                        emp_profile.uan_number = candidate.pf_uan_number
                        emp_profile.status = EmployeeProfile.Status.ACTIVE
                        emp_profile.save()

                    # Copy uploaded documents to EmployeeDocument
                    for doc in candidate.documents.all():
                        EmployeeDocument.objects.get_or_create(
                            employee=emp_profile,
                            title=doc.title,
                            defaults={
                                'file': doc.file,
                                'doc_type': 'CERTIFICATE' if doc.doc_type == 'CERTIFICATE' else 'ID_PROOF' if doc.doc_type == 'AADHAAR_CARD' else 'OTHER'
                            }
                        )

                    # 6. Update Application Status to HIRED
                    old_status = app.status
                    app.is_onboarding_completed = True
                    app.onboarding_completed_at = timezone.now()
                    app.status = JobApplication.Status.HIRED
                    app.save()

                    # 7. Audit History
                    ApplicationStatusHistory.objects.create(
                        application=app,
                        old_status=old_status,
                        new_status=JobApplication.Status.HIRED,
                        notes=f"Candidate completed full onboarding, set portal credentials (Username: {user.username}), and was activated as Employee #{emp_profile.emp_id}."
                    )

                return render(request, 'recruitment/public/onboarding_success.html', {
                    'application': app,
                    'candidate': candidate,
                    'job': app.job,
                    'user': user,
                    'employee_profile': emp_profile,
                })

            except Exception as e:
                messages.error(request, f"Error saving onboarding details: {str(e)}")
        else:
            messages.error(request, "Please check the highlighted errors in the onboarding form.")
    else:
        # Pre-populate form with existing candidate data
        initial_data = {
            'username': candidate.email.split('@')[0].replace('.', '_').replace('-', '_'),
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

    return render(request, 'recruitment/public/onboarding.html', {
        'form': form,
        'application': app,
        'candidate': candidate,
        'job': app.job,
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
