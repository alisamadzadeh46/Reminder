from django.urls import path
from .views import upload_meeting_attachment, upload_task_attachment

urlpatterns = [
    path("meeting/<int:meeting_id>/upload/", upload_meeting_attachment, name="meeting-attachment-upload"),
    path("task/<int:task_id>/upload/", upload_task_attachment, name="task-attachment-upload"),
]
