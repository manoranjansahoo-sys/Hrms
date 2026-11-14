from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', RedirectView.as_view(pattern_name='accounts:login', permanent=False)),
    path('accounts/', include('accounts.urls')),
    path('employees/', include('employees.urls')),
    path('attendance/', include('attendance.urls')),
    path('leave/', include('leave_management.urls')),
    path('payroll/', include('payroll.urls')),
    path('performance/', include('performance.urls')),
    path('support/', include('support.urls')),
    path('notifications/', include('notifications.urls')),
    path('master-data/', include('organization.urls')),
    path('', include('recruitment.urls')),
    path('', include('portal.urls')),
]

# Ensure media and static files are always served on local / dev environments
if settings.DEBUG or not settings.FORCE_SCRIPT_NAME:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATICFILES_DIRS[0]}),
    ]
else:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
