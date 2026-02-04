from django.db import models
from django.conf import settings
from meetings.models import Meeting

class Task(models.Model):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("INPROGRESS", "In Progress"),
        ("DONE", "Done"),
        ("VERIFIED", "Verified"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    meeting = models.ForeignKey(Meeting, on_delete=models.SET_NULL, null=True, blank=True, related_name="tasks")

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assigned_tasks")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_tasks")

    due_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="OPEN")

    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="followed_tasks", null=True, blank=True
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="task_approvals", null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["due_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["assignee"]),
        ]

    def __str__(self):
        return self.title
