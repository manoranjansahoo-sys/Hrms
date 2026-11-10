from django.urls import path
from django.views.generic import TemplateView
from recruitment import views
from recruitment import google_auth

app_name = 'recruitment'

urlpatterns = [
    path('privacy-policy/', TemplateView.as_view(template_name='recruitment/public/privacy_policy.html'), name='privacy_policy'),
    path('terms/', TemplateView.as_view(template_name='recruitment/public/terms.html'), name='terms'),
    path('candidate/google/verify/', google_auth.google_verify, name='google_verify'),
    path('candidate/google/reset/', google_auth.google_reset, name='google_reset'),
    # 1. HR Link & Recruitment Management
    path('hr/candidate-links/', views.candidate_links_list, name='links_list'),
    path('hr/candidate-links/create/', views.create_candidate_link, name='create_link'),
    path('hr/candidate-links/<int:link_id>/toggle/', views.toggle_candidate_link, name='toggle_link'),

    # HR Job Openings Management
    path('hr/jobs/', views.jobs_list, name='jobs_list'),
    path('hr/jobs/create/', views.create_job_opening, name='create_job'),
    path('hr/jobs/<int:job_id>/edit/', views.edit_job_opening, name='edit_job'),
    path('hr/locations/manage/', views.locations_manager, name='locations_manager'),
    path('hr/locations/add/', views.add_location, name='add_location'),
    path('hr/locations/<int:site_id>/delete/', views.delete_location, name='delete_location'),

    # HR Candidate Applications Review & Interview Scheduling
    path('hr/candidates/', views.candidates_list, name='candidates_list'),
    path('hr/candidates/export-csv/', views.export_candidates_csv, name='export_candidates_csv'),
    path('hr/candidates/<int:application_id>/', views.candidate_detail, name='candidate_detail'),
    path('hr/candidates/<int:application_id>/convert-employee/', views.convert_to_employee, name='convert_to_employee'),

    # 2. Public Candidate Registration Portal (No Login Required - Google Form Style)
    path('candidate/apply/', views.candidate_register, name='candidate_apply'),
    path('candidate/fast-apply/', views.candidate_fast_apply, name='candidate_fast_apply'),
    path('candidate/fast-apply/<int:job_id>/', views.candidate_fast_apply, name='candidate_fast_apply_job'),
    path('candidate/register/', views.candidate_register, name='candidate_register_general'),
    path('candidate/register/<str:token>/', views.candidate_register, name='candidate_register'),
    path('candidate/success/<str:application_id>/', views.candidate_success, name='candidate_success'),
    path('candidate/track/', views.candidate_track, name='candidate_track'),
    path('candidate/track/<str:application_id>/', views.candidate_track, name='candidate_track_id'),

    # 3. Post-Interview Qualified Candidate Onboarding
    path('candidate/onboarding/<str:application_id>/', views.candidate_onboarding, name='candidate_onboarding'),
]

