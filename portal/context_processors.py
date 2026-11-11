from notifications.models import Notification
from leave_management.models import LeaveRequest
from attendance.models import AttendanceCorrectionRequest
from employees.models import ProfileCorrectionRequest


def hrms_global_context(request):
    """
    Global context processor providing notifications count,
    pending badge numbers for managers/HR/Head, and role flags.
    """
    context = {
        'unread_notifications_count': 0,
        'recent_notifications': [],
        'pending_leaves_count': 0,
        'pending_corrections_count': 0,
        'pending_profile_requests_count': 0,
        'user_today_attendance': None,
        'today_attendance': None,
    }

    if request.user.is_authenticated:
        # Notifications
        notifs = Notification.objects.filter(recipient=request.user)
        context['unread_notifications_count'] = notifs.filter(is_read=False).count()
        context['recent_notifications'] = notifs[:5]

        # Role-based pending approvals counters
        user = request.user
        if user.is_head_role or user.is_hr_role:
            context['pending_leaves_count'] = LeaveRequest.objects.filter(
                status__in=[LeaveRequest.Status.PENDING_HR, LeaveRequest.Status.PENDING_MANAGER]
            ).count()
            context['pending_corrections_count'] = AttendanceCorrectionRequest.objects.filter(
                status='PENDING'
            ).count()
            context['pending_profile_requests_count'] = ProfileCorrectionRequest.objects.filter(
                status='PENDING'
            ).count()
        elif user.is_site_manager_role:
            # Site Manager gets counts for their site
            managed_sites = user.managed_sites.all()
            context['pending_leaves_count'] = LeaveRequest.objects.filter(
                status=LeaveRequest.Status.PENDING_MANAGER,
                employee__site__in=managed_sites
            ).count()
            context['pending_corrections_count'] = AttendanceCorrectionRequest.objects.filter(
                status='PENDING',
                employee__site__in=managed_sites
            ).count()

        # Today's attendance for the logged-in employee (available across all templates)
        emp = getattr(user, 'employee_profile', None)
        if emp:
            from django.utils import timezone
            from attendance.models import Attendance
            att = Attendance.objects.filter(
                employee=emp,
                date=timezone.localdate()
            ).first()
            context['user_today_attendance'] = att
            context['today_attendance'] = att

    return context

