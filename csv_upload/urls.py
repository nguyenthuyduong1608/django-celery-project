from django.urls import path
from . import views

urlpatterns = [
    path('upload-csv/', views.upload_csv, name='upload_csv'),
    path('perform-operation/', views.perform_operation, name='perform_operation'),
    path('task-status/', views.task_status, name='task_status'),
]
