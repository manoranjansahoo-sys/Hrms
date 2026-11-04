from django.urls import path
from portal import views

app_name = 'portal'

urlpatterns = [
    path('', views.smart_dashboard, name='smart_dashboard'),
    path('home/', views.company_home_portal, name='home'),
    path('dashboard/employee/', views.dashboard_employee, name='dashboard_employee'),
    path('dashboard/hr/', views.dashboard_hr, name='dashboard_hr'),
    path('dashboard/site-manager/', views.dashboard_site_manager, name='dashboard_site_manager'),
    path('dashboard/head/', views.dashboard_head, name='dashboard_head'),

    # Events & Celebrations
    path('events/', views.events_list, name='events_list'),
    path('events/<int:event_id>/register/', views.register_event, name='register_event'),

    # Holidays & Policies
    path('holidays/', views.holidays_list, name='holidays_list'),
    path('policies/', views.policies_list, name='policies_list'),
    path('policies/<int:policy_id>/acknowledge/', views.acknowledge_policy, name='acknowledge_policy'),
]

