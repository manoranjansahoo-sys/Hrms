from django.urls import path
from organization import views

app_name = 'organization'

urlpatterns = [
    # Master Data Control Center Dashboard
    path('', views.master_data_dashboard, name='master_data'),

    # Holidays Management
    path('holidays/create/', views.holiday_create, name='holiday_create'),
    path('holidays/<int:holiday_id>/edit/', views.holiday_edit, name='holiday_edit'),
    path('holidays/<int:holiday_id>/delete/', views.holiday_delete, name='holiday_delete'),

    # Operating Timings (Day-by-Day & All-Days Batch)
    path('timings/batch-update/', views.timing_batch_update, name='timing_batch_update'),
    path('timings/<int:schedule_id>/update/', views.timing_day_update, name='timing_day_update'),

    # Company Locations Management (Add, Edit, Delete)
    path('locations/create/', views.location_create, name='location_create'),
    path('locations/<int:site_id>/edit/', views.location_edit, name='location_edit'),
    path('locations/<int:site_id>/delete/', views.location_delete, name='location_delete'),

    # Leave Policies (Sick Leave & Paid Leave Quotas)
    path('leaves/<int:leave_type_id>/update/', views.leave_policy_update, name='leave_policy_update'),
    path('leaves/create/', views.leave_type_create, name='leave_type_create'),

    # Access Delegation (Admin Only)
    path('permissions/update/', views.permissions_update, name='permissions_update'),
]

