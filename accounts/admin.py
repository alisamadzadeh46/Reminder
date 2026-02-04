from django.contrib import admin
from .models import OrganizationUnit, UserProfile

@admin.register(OrganizationUnit)
class OrganizationUnitAdmin(admin.ModelAdmin):
    list_display = ("name", "parent")
    search_fields = ("name",)
    autocomplete_fields = ("parent",)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "org_unit", "phone")
    search_fields = ("user__username", "user__email", "phone")
    autocomplete_fields = ("user", "org_unit")
