from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from organization.models import MasterDataPermission


def master_data_access_required(section=None):
    """
    Decorator for views controlling access to Master Data.
    Allows Head/Super Admin by default, or HR Administrators / designated users
    delegated access by Admin.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Please log in to access Master Data.")
                return redirect('accounts:login')

            if MasterDataPermission.can_user_access(request.user, section=section):
                return view_func(request, *args, **kwargs)

            messages.error(request, "Access Restricted: Master Data Control Center is restricted to authorized Administrators. Please request access from the System Head.")
            raise PermissionDenied("You do not have permission to view or modify company Master Data.")
        return _wrapped
    return decorator

