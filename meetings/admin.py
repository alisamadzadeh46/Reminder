from django.contrib import admin, messages
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from .models import Meeting, Invitation, AgendaItem, Minutes
from .services import send_meeting_invitation


class AgendaInline(admin.TabularInline):
    model = AgendaItem
    extra = 1


class InvitationInline(admin.TabularInline):
    model = Invitation
    extra = 1
    autocomplete_fields = ["invitee"]
    fields = ("invitee", "rsvp_status", "reminder_enabled", "invited_at")
    readonly_fields = ("invited_at",)


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("title", "start_at", "end_at", "status", "secretary", "follow_up_owner", "approver")
    list_filter = ("status", "start_at")
    search_fields = ("title", "description", "location")
    autocomplete_fields = ("secretary", "follow_up_owner", "approver")
    date_hierarchy = "start_at"

    inlines = [AgendaInline, InvitationInline]
    actions = ["action_send_invitations", "action_set_scheduled", "action_set_held"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        u = request.user
        if u.is_superuser:
            return qs
        return qs.filter(
            Q(created_by=u) |
            Q(secretary=u) |
            Q(follow_up_owner=u) |
            Q(approver=u) |
            Q(invitations__invitee=u)
        ).distinct()

    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        u = request.user
        return (
            obj.created_by_id == u.id or
            obj.secretary_id == u.id or
            obj.follow_up_owner_id == u.id or
            obj.approver_id == u.id or
            obj.invitations.filter(invitee=u).exists()
        )

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        # تغییر کلی جلسه فقط creator
        return obj.created_by_id == request.user.id

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="ارسال دعوتنامه به افراد این جلسه")
    def action_send_invitations(self, request, queryset):
        sent, failed = 0, 0
        for meeting in queryset:
            for inv in meeting.invitations.select_related("invitee").all():
                if not inv.invitee.email:
                    failed += 1
                    continue
                try:
                    send_meeting_invitation(inv)
                    sent += 1
                except Exception:
                    failed += 1
        if sent:
            self.message_user(request, f"{sent} دعوتنامه ارسال شد.", level=messages.SUCCESS)
        if failed:
            self.message_user(request, f"{failed} مورد ارسال نشد (ایمیل خالی یا خطا).", level=messages.WARNING)

    @admin.action(description="تغییر وضعیت جلسه به Scheduled")
    def action_set_scheduled(self, request, queryset):
        updated = queryset.update(status="SCHEDULED")
        self.message_user(request, f"{updated} جلسه Scheduled شد.", level=messages.SUCCESS)

    @admin.action(description="تغییر وضعیت جلسه به Held")
    def action_set_held(self, request, queryset):
        updated = queryset.update(status="HELD")
        self.message_user(request, f"{updated} جلسه Held شد.", level=messages.SUCCESS)


@admin.register(AgendaItem)
class AgendaItemAdmin(admin.ModelAdmin):
    list_display = ("title", "meeting", "order")
    search_fields = ("title", "description", "meeting__title")
    list_filter = ("meeting__start_at",)
    autocomplete_fields = ("meeting",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        u = request.user
        if u.is_superuser:
            return qs
        return qs.filter(Q(meeting__secretary=u) | Q(meeting__created_by=u)).distinct()

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        u = request.user
        return obj.meeting.secretary_id == u.id or obj.meeting.created_by_id == u.id


@admin.register(Minutes)
class MinutesAdmin(admin.ModelAdmin):
    list_display = ("meeting", "status", "submitted_by", "approved_by", "approved_at")
    list_filter = ("status",)
    search_fields = ("meeting__title", "content")
    autocomplete_fields = ("meeting", "submitted_by", "approved_by")
    actions = ["submit_minutes", "approve_minutes", "reject_minutes"]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        u = request.user
        if u.is_superuser:
            return qs
        return qs.filter(
            Q(meeting__secretary=u) |
            Q(meeting__approver=u) |
            Q(meeting__created_by=u) |
            Q(meeting__invitations__invitee=u)
        ).distinct()

    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if obj is None:
            return True
        u = request.user
        # بعد از Submitted/Approved دیگر قابل ویرایش نیست
        if obj.status in ("SUBMITTED", "APPROVED"):
            return False
        return obj.meeting.secretary_id == u.id or obj.submitted_by_id == u.id

    @admin.action(description="ارسال صورتجلسه برای تایید (Submitted)")
    def submit_minutes(self, request, queryset):
        for m in queryset:
            if not (request.user.is_superuser or m.meeting.secretary_id == request.user.id):
                raise PermissionDenied("Only meeting secretary can submit minutes.")
            m.status = "SUBMITTED"
            m.save(update_fields=["status"])

    @admin.action(description="تایید صورتجلسه (Approved)")
    def approve_minutes(self, request, queryset):
        now = timezone.now()
        for m in queryset:
            if not (request.user.is_superuser or m.meeting.approver_id == request.user.id):
                raise PermissionDenied("Only meeting approver can approve minutes.")
            m.status = "APPROVED"
            m.approved_by = request.user
            m.approved_at = now
            m.save(update_fields=["status", "approved_by", "approved_at"])

    @admin.action(description="رد صورتجلسه (Rejected)")
    def reject_minutes(self, request, queryset):
        for m in queryset:
            if not (request.user.is_superuser or m.meeting.approver_id == request.user.id):
                raise PermissionDenied("Only meeting approver can reject minutes.")
            m.status = "REJECTED"
            m.save(update_fields=["status"])
