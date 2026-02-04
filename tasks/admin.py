from django.contrib import admin
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "meeting", "assignee", "status", "due_date", "follower", "approver", "created_by")
    list_filter = ("status", "due_date")
    search_fields = ("title", "description", "meeting__title", "assignee__username")
    autocomplete_fields = ("meeting", "assignee", "created_by", "follower", "approver")
    actions = ["set_inprogress", "set_done", "set_verified", "approve", "reject"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        u = request.user
        if u.is_superuser:
            return qs
        return qs.filter(
            Q(created_by=u) |
            Q(assignee=u) |
            Q(follower=u) |
            Q(approver=u) |
            Q(meeting__follow_up_owner=u) |
            Q(meeting__secretary=u) |
            Q(meeting__created_by=u)
        ).distinct()

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        u = request.user
        # تغییر فیلدها: creator یا assignee
        return obj.created_by_id == u.id or obj.assignee_id == u.id

    @admin.action(description="In Progress")
    def set_inprogress(self, request, queryset):
        for t in queryset:
            if not (request.user.is_superuser or t.assignee_id == request.user.id or t.created_by_id == request.user.id):
                raise PermissionDenied("Only assignee/creator can set In Progress.")
            t.status = "INPROGRESS"
            t.save(update_fields=["status"])

    @admin.action(description="Done")
    def set_done(self, request, queryset):
        for t in queryset:
            if not (request.user.is_superuser or t.assignee_id == request.user.id):
                raise PermissionDenied("Only assignee can set Done.")
            t.status = "DONE"
            t.save(update_fields=["status"])

    @admin.action(description="Verified (پیگیری)")
    def set_verified(self, request, queryset):
        for t in queryset:
            can = (
                request.user.is_superuser or
                t.follower_id == request.user.id or
                (t.meeting_id and t.meeting.follow_up_owner_id == request.user.id)
            )
            if not can:
                raise PermissionDenied("Only follower/follow-up owner can verify.")
            t.status = "VERIFIED"
            t.save(update_fields=["status"])

    @admin.action(description="Approve")
    def approve(self, request, queryset):
        for t in queryset:
            can = (
                request.user.is_superuser or
                t.approver_id == request.user.id or
                (t.meeting_id and t.meeting.approver_id == request.user.id)
            )
            if not can:
                raise PermissionDenied("Only approver can approve.")
            t.status = "APPROVED"
            t.save(update_fields=["status"])

    @admin.action(description="Reject")
    def reject(self, request, queryset):
        for t in queryset:
            can = (
                request.user.is_superuser or
                t.approver_id == request.user.id or
                (t.meeting_id and t.meeting.approver_id == request.user.id)
            )
            if not can:
                raise PermissionDenied("Only approver can reject.")
            t.status = "REJECTED"
            t.save(update_fields=["status"])
