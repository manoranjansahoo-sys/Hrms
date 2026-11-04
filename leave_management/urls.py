from django.urls import path
from leave_management import views

app_name = 'leave_management'

urlpatterns = [
    path('apply/', views.apply_leave, name='apply_leave'),
    path('my/', views.my_leaves, name='my_leaves'),
    path('cancel/<int:request_id>/', views.cancel_leave, name='cancel_leave'),
    path('requests/', views.leave_requests_admin, name='admin_queue'),
    path('requests/<int:request_id>/process/', views.process_leave, name='process_leave'),
    path('calendar/', views.leave_calendar_view, name='leave_calendar'),
]

