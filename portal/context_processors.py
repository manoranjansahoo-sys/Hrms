import base64
from django.conf import settings
from notifications.models import Notification
from leave_management.models import LeaveRequest
from attendance.models import AttendanceCorrectionRequest
from employees.models import ProfileCorrectionRequest

_CACHED_LOGO_B64 = None

_DEFAULT_LOGO_SVG = (
    "data:image/svg+xml;utf8,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 220 48'%3E"
    "%3Crect width='220' height='48' rx='8' fill='%230f172a'/%3E"
    "%3Cg transform='translate(14, 10)'%3E"
    "%3Crect width='28' height='28' rx='6' fill='%232563eb'/%3E"
    "%3Cpath d='M8 7 h9 a4.5 4.5 0 0 1 0 9 h-9 z' fill='%23ffffff' fill-opacity='0.9'/%3E"
    "%3Cpath d='M8 13 h10 a4.5 4.5 0 0 1 0 9 h-10 z' fill='%23ffffff'/%3E"
    "%3C/g%3E"
    "%3Ctext x='54' y='30' font-family='Inter, -apple-system, sans-serif' font-size='17' font-weight='800' fill='%23ffffff' letter-spacing='0.5'%3EBRONZEGATE%3C/text%3E"
    "%3C/svg%3E"
)

def _get_company_logo_b64():
    global _CACHED_LOGO_B64
    if _CACHED_LOGO_B64 is None:
        try:
            search_paths = [
                settings.BASE_DIR / "static" / "img" / "logo.png",
                settings.BASE_DIR / "static" / "img" / "bronzegate-logo.png",
                settings.BASE_DIR / "static" / "img" / "bronzegate-login.png",
                settings.BASE_DIR / "staticfiles" / "img" / "logo.png",
                settings.BASE_DIR / "staticfiles" / "img" / "bronzegate-logo.png",
                settings.BASE_DIR / "staticfiles" / "img" / "bronzegate-login.png",
            ]
            if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
                search_paths.extend([
                    settings.STATIC_ROOT / "img" / "logo.png",
                    settings.STATIC_ROOT / "img" / "bronzegate-logo.png",
                    settings.STATIC_ROOT / "img" / "bronzegate-login.png",
                ])
            for path in search_paths:
                if path and path.exists() and path.is_file():
                    with open(path, "rb") as f:
                        file_bytes = f.read()
                        if file_bytes:
                            _CACHED_LOGO_B64 = "data:image/png;base64," + base64.b64encode(file_bytes).decode("utf-8")
                            break
        except Exception:
            pass

        if not _CACHED_LOGO_B64:
            _CACHED_LOGO_B64 = _DEFAULT_LOGO_SVG

    return _CACHED_LOGO_B64


def hrms_global_context(request):
    """
    Global context processor providing notifications count,
    pending badge numbers for managers/HR/Head, role flags, and base64 company logo.
    """
    context = {
        'company_logo_b64': _get_company_logo_b64(),
        'unread_notifications_count': 0,
        'recent_notifications': [],
        'pending_leaves_count': 0,
        'pending_corrections_count': 0,
        'pending_profile_requests_count': 0,
        'user_today_attendance': None,
        'today_attendance': None,
        'can_manage_master_data': False,
        'can_view_workforce_directory': False,
        'pending_onboarding_count': 0,
        'subpath_prefix': request.META.get('SCRIPT_NAME', '').rstrip('/'),
    }

    if request.user.is_authenticated:
        # Check Master Data management permission and Workforce Directory permission
        try:
            from organization.models import MasterDataPermission
            context['can_manage_master_data'] = MasterDataPermission.can_user_access(request.user)
            context['can_view_workforce_directory'] = MasterDataPermission.can_user_access_workforce_directory(request.user)
        except Exception:
            is_head = (request.user.is_superuser or getattr(request.user, 'role', None) == 'head')
            context['can_manage_master_data'] = is_head
            context['can_view_workforce_directory'] = is_head or (getattr(request.user, 'role', None) == 'hr')

        # Notifications
        notifs = Notification.objects.filter(recipient=request.user)
        context['unread_notifications_count'] = notifs.filter(is_read=False).count()
        context['recent_notifications'] = notifs[:5]

        # Role-based pending approvals counters
        user = request.user
        if user.is_head_role or user.is_superuser:
            # Head / Super Admin sees all pending workforce and HR requests
            context['pending_leaves_count'] = LeaveRequest.objects.filter(
                status__in=[LeaveRequest.Status.PENDING_HR, LeaveRequest.Status.PENDING_MANAGER]
            ).count()
            context['pending_corrections_count'] = AttendanceCorrectionRequest.objects.filter(
                status='PENDING'
            ).count()
            context['pending_profile_requests_count'] = ProfileCorrectionRequest.objects.filter(
                status='PENDING'
            ).count()
            try:
                from recruitment.models import JobApplication
                context['pending_onboarding_count'] = JobApplication.objects.filter(
                    status=JobApplication.Status.ONBOARDING_COMPLETED,
                    document_verification_status__in=['PENDING', 'REJECTED']
                ).count()
            except Exception:
                context['pending_onboarding_count'] = 0
        elif user.is_hr_role:
            # HR sees only regular employee requests; HR requests are routed to Admin
            from accounts.models import CustomUser
            context['pending_leaves_count'] = LeaveRequest.objects.filter(
                status__in=[LeaveRequest.Status.PENDING_HR, LeaveRequest.Status.PENDING_MANAGER]
            ).exclude(employee__user__role=CustomUser.Role.HR).exclude(employee__user=user).count()
            context['pending_corrections_count'] = AttendanceCorrectionRequest.objects.filter(
                status='PENDING'
            ).exclude(employee__user__role=CustomUser.Role.HR).exclude(employee__user=user).count()
            context['pending_profile_requests_count'] = ProfileCorrectionRequest.objects.filter(
                status='PENDING'
            ).exclude(employee__user__role=CustomUser.Role.HR).exclude(employee__user=user).count()
            try:
                from recruitment.models import JobApplication
                context['pending_onboarding_count'] = JobApplication.objects.filter(
                    status=JobApplication.Status.ONBOARDING_COMPLETED,
                    document_verification_status__in=['PENDING', 'REJECTED']
                ).count()
            except Exception:
                context['pending_onboarding_count'] = 0
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

