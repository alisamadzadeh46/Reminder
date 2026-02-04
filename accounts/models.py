from django.db import models
from django.conf import settings

class OrganizationUnit(models.Model):
    name = models.CharField(max_length=150, unique=True)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    org_unit = models.ForeignKey(OrganizationUnit, null=True, blank=True, on_delete=models.SET_NULL)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"Profile: {self.user}"
