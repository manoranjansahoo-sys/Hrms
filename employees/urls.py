from django.urls import path
from employees import views

app_name = 'employees'

urlpatterns = [
    path('', views.employee_list, name='employee_list'),
    path('add/', views.employee_create, name='employee_create'),
    path('export/csv/', views.export_employees_csv, name='export_csv'),
    path('profile-corrections/', views.profile_corrections_list, name='profile_corrections_list'),
    path('profile-corrections/request/', views.profile_correction_request, name='profile_correction_request'),
    path('profile-corrections/<int:request_id>/review/', views.review_profile_correction, name='review_profile_correction'),
    path('<str:emp_id>/', views.employee_detail, name='employee_detail'),
]

