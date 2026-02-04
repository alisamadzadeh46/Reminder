from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.conf import settings

class Attachment(models.Model):
    title = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to="attachments/%Y/%m/")

    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    class Meta:
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["uploaded_at"]),
        ]

    def __str__(self):
        return self.title or self.file.name
