from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_list, name='project_list'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('projects/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('projects/<int:project_id>/files/create/', views.create_file, name='create_file'),
    path('projects/<int:project_id>/files/<int:file_id>/', views.code_editor, name='code_editor'),
    path('projects/<int:project_id>/files/<int:file_id>/save/', views.save_file, name='save_file'),
    path('projects/<int:project_id>/files/<int:file_id>/history/', views.file_history, name='file_history'),
    path('projects/<int:project_id>/files/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    path('projects/<int:project_id>/invite/', views.invite_member, name='invite_member'),
    path('projects/<int:project_id>/members/', views.project_members, name='project_members'),
    path('projects/<int:project_id>/members/remove/<int:user_id>/', views.remove_member, name='remove_member'),
    path('projects/<int:project_id>/tasks/', views.task_list, name='task_list'),
    path('projects/<int:project_id>/tasks/create/', views.create_task, name='create_task'),
    path('projects/<int:project_id>/tasks/<int:task_id>/', views.task_detail, name='task_detail'),
    path('projects/<int:project_id>/tasks/<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('projects/<int:project_id>/tasks/<int:task_id>/delete/', views.delete_task, name='delete_task'),
    path('projects/<int:project_id>/request/', views.request_to_join, name='request_to_join'),
    path('requests/<int:request_id>/handle/', views.handle_join_request, name='handle_join_request'),
]
