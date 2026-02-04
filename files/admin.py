from django.contrib import admin
from .models import Attachment

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "file", "uploaded_by", "uploaded_at", "content_type", "object_id")
    list_filter = ("content_type", "uploaded_at")
    search_fields = ("title", "file")
    autocomplete_fields = ("uploaded_by",)
