from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from accounts.models import CustomUser


def role_required(allowed_roles):
    """
    Decorator for views that checks whether a user has one of the allowed roles.
    Allowed roles can be single string or list/tuple of strings.
    Superusers automatically pass.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Please log in to access this page.")
                return redirect('accounts:login')

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)

            messages.error(request, "Access Denied: You do not have permission to view this resource.")
            raise PermissionDenied("You do not have access to this resource.")
        return _wrapped_view
    return decorator


def hr_required(view_func):
    """Allows HR, Head, or Superuser."""
    return role_required([CustomUser.Role.HR, CustomUser.Role.HEAD])(view_func)


def head_required(view_func):
    """Allows Head or Superuser."""
    return role_required([CustomUser.Role.HEAD])(view_func)


def site_manager_required(view_func):
    """Allows Site Manager, HR, Head, or Superuser."""
    return role_required([CustomUser.Role.SITE_MANAGER, CustomUser.Role.HR, CustomUser.Role.HEAD])(view_func)


def employee_required(view_func):
    """Allows any authenticated employee / user."""
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to continue.")
            return redirect('accounts:login')
        return view_func(request, *args, **kwargs)
    return _wrapped


def log_audit_trail(action, module, description, user=None, ip_address=None):
    from accounts.models import AuditLog
    try:
        if hasattr(ip_address, 'META'):
            req = ip_address
            ip = req.META.get('HTTP_X_FORWARDED_FOR', req.META.get('REMOTE_ADDR', ''))
            if ip and ',' in ip:
                ip = ip.split(',')[0].strip()
            ip_address = ip or None
        elif ip_address:
            ip_address = str(ip_address)[:45]

        AuditLog.objects.create(
            user=user if user and user.is_authenticated else None,
            action=action,
            module=module,
            description=description,
            ip_address=ip_address
        )
    except Exception:
        pass

