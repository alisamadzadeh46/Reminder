from django.urls import path
from .views import *

urlpatterns = [
    path("my/", my_tasks, name="my-tasks"),
    path("create/", task_create, name="task-create"),
    path("<int:pk>/status/", task_change_status, name="task-change-status"),
]
