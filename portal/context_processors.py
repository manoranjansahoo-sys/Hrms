import base64
from pathlib import Path
from django.conf import settings
from django.contrib.staticfiles.finders import find as find_static
from notifications.models import Notification
from leave_management.models import LeaveRequest
from attendance.models import AttendanceCorrectionRequest
from employees.models import ProfileCorrectionRequest

_CACHED_LOGO_B64 = None

_DEFAULT_LOGO_SVG = (
    "data:image/svg+xml;base64,"
    "PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyMjAgNDgiIHdpZHRoPSIyMjAiIGhlaWdodD0iNDgiPgogIDxyZWN0IHdpZHRoPSIyMjAiIGhlaWdodD0iNDgiIHJ4PSI4IiBmaWxsPSIjMGYxNzJhIi8+CiAgPGcgdHJhbnNmb3JtPSJ0cmFuc2xhdGUoMTQsIDEwKSI+CiAgICA8cmVjdCB3aWR0aD0iMjgiIGhlaWdodD0iMjgiIHJ4PSI2IiBmaWxsPSIjMjU2M2ViIi8+CiAgICA8cGF0aCBkPSJNOCA3IGg5IGE0LjUgNC41IDAgMCAxIDAgOSBoLTkgeiIgZmlsbD0iI2ZmZmZmZiIgZmlsbC1vcGFjaXR5PSIwLjkiLz4KICAgIDxwYXRoIGQ9Ik04IDEzIGgxMCBhNC41IDQuNSAwIDAgMSAwIDkgaC0xMCB6IiBmaWxsPSIjZmZmZmZmIi8+CiAgPC9nPgogIDx0ZXh0IHg9IjU0IiB5PSIzMCIgZm9udC1mYW1pbHk9IkludGVyLCAtYXBwbGUtc3lzdGVtLCBzYW5zLXNlcmlmIiBmb250LXNpemU9IjE3IiBmb250LXdlaWdodD0iODAwIiBmaWxsPSIjZmZmZmZmIiBsZXR0ZXItc3BhY2luZz0iMC41Ij5CUk9OWkVHQVRFPC90ZXh0Pgo8L3N2Zz4="
)

def _get_company_logo_b64():
    global _CACHED_LOGO_B64
    if _CACHED_LOGO_B64 is None:
        try:
            candidates = [
                "img/logo.png",
                "img/bronzegate-logo.png",
                "img/bronzegate-login.png",
            ]
            file_found = None
            # 1. Try Django static finder
            for candidate in candidates:
                try:
                    found = find_static(candidate)
                    if found and Path(found).is_file():
                        file_found = Path(found)
                        break
                except Exception:
                    pass

            # 2. Try explicit directories
            if not file_found:
                search_dirs = [
                    settings.BASE_DIR / "static",
                    settings.BASE_DIR / "staticfiles",
                ]
                if hasattr(settings, 'STATIC_ROOT') and settings.STATIC_ROOT:
                    search_dirs.append(Path(settings.STATIC_ROOT))

                for sdir in search_dirs:
                    if sdir and sdir.exists():
                        for candidate in candidates:
                            cand_path = sdir / candidate
                            if cand_path.is_file():
                                file_found = cand_path
                                break
                    if file_found:
                        break

            if file_found and file_found.is_file():
                with open(file_found, "rb") as f:
                    file_bytes = f.read()
                    if file_bytes:
                        _CACHED_LOGO_B64 = "data:image/png;base64," + base64.b64encode(file_bytes).decode("utf-8")
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
        'pending_document_requests_count': 0,
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
                from support.models import OfficialDocumentRequest
                context['pending_document_requests_count'] = OfficialDocumentRequest.objects.filter(
                    status='PENDING'
                ).count()
            except Exception:
                context['pending_document_requests_count'] = 0
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
                from support.models import OfficialDocumentRequest
                context['pending_document_requests_count'] = OfficialDocumentRequest.objects.filter(
                    status='PENDING'
                ).exclude(employee__user__role=CustomUser.Role.HR).exclude(employee__user=user).count()
            except Exception:
                context['pending_document_requests_count'] = 0
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

