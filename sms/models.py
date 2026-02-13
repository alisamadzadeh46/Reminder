from django.conf import settings
from django.db import models
from django.utils import timezone


class SMSStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    QUEUED = "QUEUED", "Queued"
    SENT = "SENT", "Sent"
    FAILED = "FAILED", "Failed"



class SMSTemplateKey(models.TextChoices):
    MEETING_INVITE = "MEETING_INVITE", "Meeting Invite"
    MEETING_REMINDER = "MEETING_REMINDER", "Meeting Reminder"
    TASK_ASSIGNED = "TASK_ASSIGNED", "Task Assigned"
    TASK_DUE_48H = "TASK_DUE_48H", "Task Due (48h)"
    TASK_OVERDUE = "TASK_OVERDUE", "Task Overdue"


class SMSTemplate(models.Model):
    key = models.CharField(max_length=64, choices=SMSTemplateKey.choices, unique=True)
    title = models.CharField(max_length=200)
    body = models.TextField(help_text="از متغیرها مثل {meeting_title} استفاده کنید.")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SMS Template"
        verbose_name_plural = "SMS Templates"

    def __str__(self):
        return f"{self.key} - {self.title}"


class SMSProviderSettings(models.Model):
    PROVIDER_CHOICES = (
        ("PAYAMAKVIP", "Payamak.vip"),
        ("FAKE", "Fake (Test)"),
    )

    provider = models.CharField(max_length=32, choices=PROVIDER_CHOICES, default="FAKE")
    is_enabled = models.BooleanField(default=True)

    # Payamak.vip settings
    base_url = models.CharField(
        max_length=255,
        blank=True,
        default="http://www.payamak.vip/api/v1/RestWebApi/"
    )
    username = models.CharField(max_length=128, blank=True, default="")
    password = models.CharField(max_length=128, blank=True, default="")
    from_number = models.CharField(max_length=50, blank=True, default="")

    is_flash = models.BooleanField(default=False)
    send_delay = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "SMS Provider Settings"
        verbose_name_plural = "SMS Provider Settings"

    def __str__(self):
        return f"{self.provider} (enabled={self.is_enabled})"


class OutboundSMS(models.Model):
    template = models.ForeignKey(SMSTemplate, null=True, blank=True, on_delete=models.SET_NULL)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    to = models.CharField(max_length=40)
    body = models.TextField()

    status = models.CharField(max_length=16, choices=SMSStatus.choices, default=SMSStatus.QUEUED)
    attempts = models.PositiveIntegerField(default=0)

    idempotency_key = models.CharField(max_length=128, blank=True, default="", db_index=True)

    provider_message_id = models.CharField(max_length=128, blank=True, default="")
    provider_response = models.TextField(blank=True, default="")
    error = models.TextField(blank=True, default="")

    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Outbound SMS"
        verbose_name_plural = "Outbound SMS"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["to", "created_at"]),
        ]

    def __str__(self):
        return f"{self.to} - {self.status}"

    def mark_sent(self, provider_message_id: str = "", provider_response: str = ""):
        self.status = SMSStatus.SENT
        self.sent_at = timezone.now()
        self.provider_message_id = provider_message_id or ""
        self.provider_response = provider_response or ""
        self.error = ""
        self.save(update_fields=["status", "sent_at", "provider_message_id", "provider_response", "error"])

    def mark_failed(self, error: str, provider_response: str = ""):
        self.status = SMSStatus.FAILED
        self.error = error or "Unknown error"
        self.provider_response = provider_response or ""
        self.save(update_fields=["status", "error", "provider_response"])