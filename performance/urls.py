from django.urls import path
from performance import views

app_name = 'performance'

urlpatterns = [
    path('goals/', views.goals_list, name='goals_list'),
    path('goals/assign/', views.assign_goal, name='assign_goal'),
    path('goals/<int:goal_id>/update/', views.update_goal_progress, name='update_goal'),
    path('reviews/', views.reviews_list, name='reviews_list'),
    path('reviews/create/', views.create_review, name='create_review'),
]

