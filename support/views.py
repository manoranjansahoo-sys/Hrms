from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from accounts.models import CustomUser
from accounts.decorators import role_required, hr_required, log_audit_trail
from support.models import SupportTicket, TicketComment, OfficialDocumentRequest, Asset
from employees.models import EmployeeProfile
from notifications.models import create_notification


@login_required
def tickets_list(request):
    """View IT support tickets & employee grievances."""
    user = request.user
    emp_profile = getattr(user, 'employee_profile', None)

    if user.is_hr_role or user.is_head_role or user.is_superuser:
        tickets = SupportTicket.objects.select_related('employee__user').all()
    else:
        tickets = SupportTicket.objects.filter(employee=emp_profile).select_related('employee__user')

    return render(request, 'support/tickets_list.html', {'tickets': tickets})


@login_required
def create_ticket(request):
    """Employee submits a new ticket or grievance."""
    emp = getattr(request.user, 'employee_profile', None)
    if not emp:
        messages.error(request, "Employee profile required.")
        return redirect('portal:smart_dashboard')

    if request.method == 'POST':
        category = request.POST.get('category')
        priority = request.POST.get('priority', 'MEDIUM')
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        attachment = request.FILES.get('attachment')

        ticket = SupportTicket.objects.create(
            employee=emp,
            category=category,
            priority=priority,
            subject=subject,
            description=description,
            attachment=attachment,
            status='OPEN'
        )

        messages.success(request, f"Ticket #{ticket.id} submitted successfully.")
        return redirect('support:ticket_detail', ticket_id=ticket.id)

    return render(request, 'support/ticket_form.html')


@login_required
def ticket_detail(request, ticket_id):
    """View ticket discussion thread and update status."""
    ticket = get_object_or_404(SupportTicket.objects.select_related('employee__user'), id=ticket_id)
    user = request.user

    # Security check: Only ticket owner or HR/Head can view
    is_owner = (ticket.employee.user == user)
    if not (is_owner or user.is_hr_role or user.is_head_role or user.is_superuser):
        messages.error(request, "Permission denied to view this ticket.")
        return redirect('support:tickets_list')

    if request.method == 'POST':
        # Post comment
        comment_text = request.POST.get('comment', '').strip()
        new_status = request.POST.get('status')

        if comment_text:
            TicketComment.objects.create(ticket=ticket, user=user, comment=comment_text)

        if new_status and (user.is_hr_role or user.is_head_role or user.is_superuser):
            ticket.status = new_status
            if new_status in ['RESOLVED', 'CLOSED']:
                ticket.resolved_at = timezone.now()
            ticket.save()
            messages.success(request, f"Ticket #{ticket.id} status updated to {ticket.get_status_display()}.")

        return redirect('support:ticket_detail', ticket_id=ticket.id)

    comments = ticket.comments.select_related('user').all()
    return render(request, 'support/ticket_detail.html', {
        'ticket': ticket,
        'comments': comments,
        'is_admin': user.is_hr_role or user.is_head_role,
    })


@login_required
def document_requests_view(request):
    """View and submit requests for official employment certificates."""
    user = request.user
    emp_profile = getattr(user, 'employee_profile', None)

    if request.method == 'POST':
        doc_type = request.POST.get('document_type')
        purpose = request.POST.get('purpose')

        doc_req = OfficialDocumentRequest.objects.create(
            employee=emp_profile,
            document_type=doc_type,
            purpose=purpose,
            status='PENDING'
        )

        # Notify HR
        hr_users = CustomUser.objects.filter(role=CustomUser.Role.HR)
        for h in hr_users:
            create_notification(
                recipient=h,
                title='Official Document Request',
                message=f"{emp_profile.full_name} requested a {doc_req.get_document_type_display()}.",
                notification_type='SUPPORT',
                target_url='/support/documents/'
            )

        messages.success(request, f"Request for {doc_req.get_document_type_display()} submitted to HR.")
        return redirect('support:documents_list')

    if user.is_hr_role or user.is_head_role:
        requests_list = OfficialDocumentRequest.objects.select_related('employee__user').all()
    else:
        requests_list = OfficialDocumentRequest.objects.filter(employee=emp_profile).select_related('employee__user')

    return render(request, 'support/documents_list.html', {
        'requests_list': requests_list,
        'doc_choices': OfficialDocumentRequest.DOC_CHOICES,
        'is_hr': user.is_hr_role or user.is_head_role,
    })


@login_required
@hr_required
def process_document_request(request, request_id):
    """HR marks document request as issued or rejected."""
    doc_req = get_object_or_404(OfficialDocumentRequest, id=request_id)
    action = request.POST.get('action')
    remarks = request.POST.get('remarks', '')

    if action == 'ISSUE':
        doc_req.status = 'ISSUED'
        doc_req.reviewed_by = request.user
        doc_req.hr_remarks = remarks
        doc_req.resolved_at = timezone.now()
        doc_req.save()

        create_notification(
            recipient=doc_req.employee.user,
            title='Document Request Ready',
            message=f"Your {doc_req.get_document_type_display()} has been processed and issued.",
            notification_type='SUPPORT',
            target_url='/support/documents/'
        )
        messages.success(request, f"Document request for {doc_req.employee.full_name} marked as issued.")
    elif action == 'REJECT':
        doc_req.status = 'REJECTED'
        doc_req.reviewed_by = request.user
        doc_req.hr_remarks = remarks
        doc_req.resolved_at = timezone.now()
        doc_req.save()
        messages.info(request, f"Document request for {doc_req.employee.full_name} rejected.")

    return redirect('support:documents_list')


@login_required
def assets_list_view(request):
    """Asset management and tracking."""
    user = request.user
    emp_profile = getattr(user, 'employee_profile', None)

    if user.is_hr_role or user.is_head_role or user.is_site_manager_role:
        assets = Asset.objects.select_related('assigned_to__user').all()
    else:
        assets = Asset.objects.filter(assigned_to=emp_profile).select_related('assigned_to__user')

    return render(request, 'support/assets_list.html', {'assets': assets})
