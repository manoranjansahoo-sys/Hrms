from django.urls import path
from attendance import views

app_name = 'attendance'

urlpatterns = [
    path('punch-in/', views.punch_in_view, name='punch_in'),
    path('punch-out/', views.punch_out_view, name='punch_out'),
    path('my/', views.my_attendance, name='my_attendance'),
    path('correction/request/', views.request_attendance_correction, name='request_correction'),
    path('register/', views.attendance_admin_register, name='admin_register'),
    path('employee/<str:emp_id>/', views.employee_attendance_detail, name='employee_attendance_detail'),
    path('corrections/', views.attendance_corrections_list, name='corrections_list'),
    path('corrections/<int:request_id>/approve/', views.approve_attendance_correction, name='approve_correction'),
]

