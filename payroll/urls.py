from django.urls import path
from payroll import views

app_name = 'payroll'

urlpatterns = [
    path('', views.payroll_dashboard, name='dashboard'),
    path('my-payslips/', views.my_payslips, name='my_payslips'),
    path('payslips/<int:payslip_id>/pdf/', views.download_payslip_pdf, name='download_pdf'),
    path('generate/', views.generate_payroll_period, name='generate_payroll'),
    path('period/<int:period_id>/', views.payroll_detail, name='period_detail'),
    path('period/<int:period_id>/approve/', views.approve_payroll, name='approve_payroll'),
]

