from django.urls import path
from notifications import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notifications_list, name='list'),
    path('<int:notif_id>/read/', views.mark_notification_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
]

