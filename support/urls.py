from django.urls import path
from support import views

app_name = 'support'

urlpatterns = [
    path('tickets/', views.tickets_list, name='tickets_list'),
    path('tickets/new/', views.create_ticket, name='create_ticket'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('documents/', views.document_requests_view, name='documents_list'),
    path('documents/<int:request_id>/process/', views.process_document_request, name='process_document'),
    path('assets/', views.assets_list_view, name='assets_list'),
]

