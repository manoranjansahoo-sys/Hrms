from django.urls import path
from payroll import views

app_name = 'payroll'

urlpatterns = [
    path('', views.payroll_dashboard, name='dashboard'),
    path('my-payslips/', views.my_payslips, name='my_payslips'),
    path('payslips/<int:payslip_id>/', views.payslip_detail, name='payslip_detail'),
    path('payslips/<int:payslip_id>/pdf/', views.download_payslip_pdf, name='download_pdf'),
    path('payslips/<int:payslip_id>/condone/', views.condone_shortfall_deduction, name='condone_deduction'),
    path('generate/', views.generate_payroll_period, name='generate_payroll'),
    path('period/<int:period_id>/', views.payroll_detail, name='period_detail'),
    path('period/<int:period_id>/approve/', views.approve_payroll, name='approve_payroll'),
    path('period/<int:period_id>/export/<str:format_type>/', views.export_payroll_period_report, name='export_period_report'),
    path('period/<int:period_id>/export/', views.export_payroll_period_report, name='export_period_report_default'),
]


