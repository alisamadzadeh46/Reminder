from django.contrib import admin
from .models import SMSTemplate, OutboundSMS, SMSProviderSettings


@admin.register(SMSTemplate)
class SMSTemplateAdmin(admin.ModelAdmin):
    list_display = ("key", "title", "is_active", "updated_at")
    list_filter = ("is_active", "key")
    search_fields = ("title", "body", "key")


@admin.register(SMSProviderSettings)
class SMSProviderSettingsAdmin(admin.ModelAdmin):
    list_display = ("provider", "is_enabled", "from_number", "updated_at")
    list_filter = ("provider", "is_enabled")
    search_fields = ("provider", "username", "from_number", "base_url")
    readonly_fields = ("updated_at",)


@admin.register(OutboundSMS)
class OutboundSMSAdmin(admin.ModelAdmin):
    list_display = ("to", "status", "attempts", "template", "user", "created_at", "sent_at")
    list_filter = ("status", "template")
    search_fields = ("to", "body", "provider_message_id", "idempotency_key", "error")
    readonly_fields = (
        "status", "attempts", "provider_message_id", "provider_response", "error",
        "scheduled_at", "sent_at", "created_at"
    )