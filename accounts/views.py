import mimetypes
from django.http import FileResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from accounts.models import CustomUser, AuditLog
from accounts.forms import LoginForm, UserProfileUpdateForm
from django.contrib.auth.forms import PasswordChangeForm
from accounts.decorators import role_required, log_audit_trail


def login_view(request):
    if request.user.is_authenticated:
        return redirect('portal:smart_dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            log_audit_trail('LOGIN', 'Authentication', f"User {user.username} logged in successfully.", user=user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('portal:smart_dashboard')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    if request.user.is_authenticated:
        log_audit_trail('LOGOUT', 'Authentication', f"User {request.user.username} logged out.", user=request.user)
    logout(request)
    messages.info(request, "You have been logged out securely.")
    return redirect('accounts:login')


@login_required
def quick_switch_role(request, username):
    """
    Demo / Development helper: Allows testing between Head, HR, Site Manager, and Employee
    in one click without re-typing passwords repeatedly.
    """
    user = get_object_or_404(CustomUser, username=username)
    login(request, user)
    log_audit_trail('LOGIN', 'Demo Switcher', f"Switched active user to {user.username} ({user.role}).", user=user)
    messages.success(request, f"Switched session to {user.get_full_name()} ({user.get_role_display()})")
    return redirect('portal:smart_dashboard')


@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            log_audit_trail('UPDATE', 'User Profile', f"User {user.username} updated profile information.", user=user)
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('accounts:profile')
    else:
        form = UserProfileUpdateForm(instance=user)

    return render(request, 'accounts/profile.html', {'form': form, 'user_obj': user})


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            log_audit_trail('UPDATE', 'Security', "Password changed successfully.", user=user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please correct the error below.")
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
@role_required([CustomUser.Role.HEAD, CustomUser.Role.HR])
def audit_logs_view(request):
    logs = AuditLog.objects.select_related('user').all()
    action_filter = request.GET.get('action')
    if action_filter:
        logs = logs.filter(action=action_filter)

    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'accounts/audit_logs.html', {
        'page_obj': page_obj,
        'action_choices': AuditLog.ACTION_CHOICES,
        'selected_action': action_filter
    })


def user_avatar_view(request, user_id):
    """
    Safely stream user avatar or redirect to avatar fallback without breaking subpath or missing files.
    """
    user = get_object_or_404(CustomUser, id=user_id)
    if user.avatar:
        try:
            if user.avatar.storage.exists(user.avatar.name):
                content_type, _ = mimetypes.guess_type(user.avatar.name)
                response = FileResponse(user.avatar.open('rb'), content_type=content_type or 'image/jpeg')
                response['Cache-Control'] = 'public, max-age=86400'
                return response
        except Exception:
            pass

    from django.http import HttpResponse
    char = (user.first_name[:1] if user.first_name else (user.username[:1] if user.username else 'U')).upper()
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 128 128">'
        f'<rect width="128" height="128" rx="64" fill="#1B5E20"/>'
        f'<text x="64" y="82" font-family="Inter, -apple-system, sans-serif" font-size="56" font-weight="700" fill="#ffffff" text-anchor="middle">{char}</text>'
        f'</svg>'
    )
    response = HttpResponse(svg, content_type="image/svg+xml")
    response['Cache-Control'] = 'public, max-age=86400'
    return response

