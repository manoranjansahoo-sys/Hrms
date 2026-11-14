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
    
    # Dynamic QR Attendance System (4s Dynamic Rotation + Device GPS Geofencing 200m)
    path('kiosk/', views.qr_kiosk_view, name='qr_kiosk'),
    path('kiosk/<int:site_id>/', views.qr_kiosk_view, name='qr_kiosk_site'),
    path('kiosk/<int:site_id>/token/', views.qr_kiosk_token_api, name='qr_kiosk_token_api'),
    path('scanner/', views.qr_scanner_view, name='qr_scanner'),
    path('qr-punch/', views.qr_punch_direct, name='qr_punch_direct'),
    path('qr-punch/api/', views.qr_punch_api, name='qr_punch_api'),
    path('qr-dashboard/', views.qr_dashboard_view, name='qr_dashboard'),
    path('sites/<int:site_id>/location-config/', views.site_location_config_api, name='site_location_config_api'),
]

