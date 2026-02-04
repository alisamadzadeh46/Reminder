from django.db import models
from django.conf import settings

class Meeting(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SCHEDULED", "Scheduled"),
        ("HELD", "Held"),
        ("ARCHIVED", "Archived"),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)

    secretary = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="secretary_meetings"
    )
    follow_up_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="followup_meetings"
    )
    approver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approver_meetings"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_meetings"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["start_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.start_at:%Y-%m-%d %H:%M})"


class Invitation(models.Model):
    RSVP_CHOICES = [
        ("PENDING", "Pending"),
        ("ACCEPTED", "Accepted"),
        ("DECLINED", "Declined"),
        ("TENTATIVE", "Tentative"),
    ]

    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="invitations")
    invitee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invitations")

    rsvp_status = models.CharField(max_length=20, choices=RSVP_CHOICES, default="PENDING")
    invited_at = models.DateTimeField(null=True, blank=True)
    reminder_enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ("meeting", "invitee")
        indexes = [models.Index(fields=["rsvp_status"])]

    def __str__(self):
        return f"{self.meeting_id} -> {self.invitee_id}"


class AgendaItem(models.Model):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="agenda_items")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]
        indexes = [models.Index(fields=["meeting", "order"])]

    def __str__(self):
        return f"{self.order}. {self.title}"


class Minutes(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SUBMITTED", "Submitted"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    meeting = models.OneToOneField(Meeting, on_delete=models.CASCADE, related_name="minutes")
    content = models.TextField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_minutes"
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_minutes",
        null=True,
        blank=True
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=["status"])]

    def __str__(self):
        return f"Minutes({self.meeting_id})"
