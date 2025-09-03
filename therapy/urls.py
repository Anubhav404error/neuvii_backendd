from django.urls import path
from . import views

urlpatterns = [
    path('assign-task-wizard/', views.assign_task_wizard, name='assign_task_wizard'),
    path('api/long-term-goals/', views.get_long_term_goals, name='get_long_term_goals'),
    path('api/short-term-goals/', views.get_short_term_goals, name='get_short_term_goals'),
    path('api/tasks/', views.get_tasks, name='get_tasks'),
    path('api/assign-tasks/', views.assign_tasks, name='assign_tasks'),
]