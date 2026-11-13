from django.urls import path
from recruitment import views

app_name = 'recruitment'

urlpatterns = [
    # 1. HR Link & Recruitment Management
    path('hr/candidate-links/', views.candidate_links_list, name='links_list'),
    path('hr/candidate-links/create/', views.create_candidate_link, name='create_link'),
    path('hr/candidate-links/<int:link_id>/toggle/', views.toggle_candidate_link, name='toggle_link'),

    # HR Job Openings Management
    path('hr/jobs/', views.jobs_list, name='jobs_list'),
    path('hr/jobs/create/', views.create_job_opening, name='create_job'),
    path('hr/jobs/<int:job_id>/edit/', views.edit_job_opening, name='edit_job'),
    path('hr/api/departments/create/', views.create_department_ajax, name='create_department_ajax'),
    path('hr/locations/manage/', views.locations_manager, name='locations_manager'),
    path('hr/locations/add/', views.add_location, name='add_location'),
    path('hr/locations/<int:site_id>/delete/', views.delete_location, name='delete_location'),

    # HR Candidate Applications Review & Interview Scheduling
    path('hr/candidates/', views.candidates_list, name='candidates_list'),
    path('hr/candidates/bulk-status-update/', views.bulk_update_candidate_status, name='bulk_update_status'),
    path('hr/candidates/schedule-interview/', views.schedule_candidate_interview, name='schedule_candidate_interview'),
    path('hr/candidates/export-csv/', views.export_candidates_csv, name='export_candidates_csv'),
    path('hr/candidates/<int:application_id>/', views.candidate_detail, name='candidate_detail'),
    path('hr/candidates/<int:application_id>/convert-employee/', views.convert_to_employee, name='convert_to_employee'),

    # HR Onboarding Verification, Document Review & Appointment Pipeline
    path('hr/onboarding/', views.onboarding_candidates_list, name='onboarding_candidates_list'),
    path('hr/onboarding/appoint-employee/', views.appoint_employee, name='appoint_employee'),
    path('hr/onboarding/fetch-candidate/', views.fetch_onboarding_candidate_ajax, name='fetch_onboarding_candidate_ajax'),
    path('hr/onboarding/<str:application_id>/verify-documents/', views.verify_candidate_documents, name='verify_candidate_documents'),
    path('hr/onboarding/documents/<int:doc_id>/verify/', views.verify_single_candidate_document_ajax, name='verify_single_candidate_document'),
    path('hr/onboarding/documents/<int:doc_id>/reject/', views.reject_single_candidate_document_ajax, name='reject_single_candidate_document'),

    # 2. Public Candidate Registration Portal (No Login Required - Google Form Style)
    path('candidate/api/google-auth/', views.candidate_google_auth, name='candidate_google_auth'),
    path('candidate/api/google-logout/', views.candidate_google_logout, name='candidate_google_logout'),
    path('candidate/api/lookup/', views.candidate_lookup_ajax, name='candidate_lookup_ajax'),
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

