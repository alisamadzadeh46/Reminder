from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView, DetailView

from .models import Meeting, Invitation
from tasks.models import Task
from files.models import Attachment
from files.forms import AttachmentForm
from .forms import MeetingCreateForm, InviteeAddForm  # اگر InviteeAddForm نداری پایین‌تر می‌سازیم


User = get_user_model()


# اگر فایل meetings/forms.py فقط MeetingCreateForm دارد، این فرم را اینجا می‌سازیم که پروژه نخوابد
class _InviteeAddFormFallback(forms.Form):
    invitee_identifier = forms.CharField(
        label="نام کاربری یا ایمیل",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "username یا email"})
    )


def _can_create_meeting(user):
    # فعلاً فقط staff یا superuser (بعداً می‌تونیم group-based کنیم)
    return user.is_superuser or user.is_staff


class RSVPForm(forms.Form):
    rsvp_status = forms.ChoiceField(choices=Invitation.RSVP_CHOICES, widget=forms.Select(attrs={"class": "form-select"}))


@method_decorator(login_required, name="dispatch")
class MyMeetingsListView(ListView):
    template_name = "meetings/my_meetings_list.html"
    context_object_name = "meetings"
    paginate_by = 20

    def get_queryset(self):
        u = self.request.user
        return (
            Meeting.objects.filter(
                Q(created_by=u) |
                Q(secretary=u) |
                Q(follow_up_owner=u) |
                Q(approver=u) |
                Q(invitations__invitee=u)
            )
            .distinct()
            .order_by("-start_at")
        )


@method_decorator(login_required, name="dispatch")
class MeetingDetailView(DetailView):
    model = Meeting
    template_name = "meetings/meeting_detail.html"
    context_object_name = "meeting"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        u = self.request.user

        allowed = (
            u.is_superuser or
            obj.created_by_id == u.id or
            obj.secretary_id == u.id or
            obj.follow_up_owner_id == u.id or
            obj.approver_id == u.id or
            obj.invitations.filter(invitee=u).exists()
        )
        if not allowed:
            raise PermissionDenied("شما به این جلسه دسترسی ندارید.")
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        meeting = self.object
        u = self.request.user

        # داده‌های جلسه
        ctx["agenda_items"] = meeting.agenda_items.all()
        ctx["invitations"] = meeting.invitations.select_related("invitee").all()
        ctx["tasks"] = meeting.tasks.select_related("assignee", "created_by").all().order_by("-created_at")
        ctx["minutes"] = getattr(meeting, "minutes", None)

        # پیوست‌های جلسه (Generic FK)
        ctx["attachments"] = Attachment.objects.filter(
            content_type__model="meeting",
            object_id=meeting.id
        ).order_by("-uploaded_at")

        # فرم آپلود پیوست
        ctx["attachment_form"] = AttachmentForm()

        # RSVP
        inv = meeting.invitations.filter(invitee=u).first()
        ctx["my_invitation"] = inv
        ctx["rsvp_form"] = RSVPForm(initial={"rsvp_status": inv.rsvp_status}) if inv else None

        # فرم اضافه کردن مدعو
        try:
            ctx["invitee_form"] = InviteeAddForm()
        except Exception:
            ctx["invitee_form"] = _InviteeAddFormFallback()

        return ctx


@login_required
def meeting_rsvp(request, pk: int):
    meeting = get_object_or_404(Meeting, pk=pk)
    inv = get_object_or_404(Invitation, meeting=meeting, invitee=request.user)

    if request.method == "POST":
        form = RSVPForm(request.POST)
        if form.is_valid():
            inv.rsvp_status = form.cleaned_data["rsvp_status"]
            inv.save(update_fields=["rsvp_status"])
            messages.success(request, "RSVP ثبت شد.")
        else:
            messages.error(request, "فرم RSVP معتبر نیست.")

    return redirect("meeting-detail", pk=meeting.pk)


@method_decorator(login_required, name="dispatch")
class MeetingCreateView(View):
    template_name = "meetings/meeting_create.html"

    def get(self, request):
        if not _can_create_meeting(request.user):
            raise PermissionDenied("اجازه ایجاد جلسه ندارید.")
        return render(request, self.template_name, {"form": MeetingCreateForm()})

    def post(self, request):
        if not _can_create_meeting(request.user):
            raise PermissionDenied("اجازه ایجاد جلسه ندارید.")

        form = MeetingCreateForm(request.POST)
        if form.is_valid():
            meeting = form.save(commit=False)
            meeting.created_by = request.user
            meeting.status = "DRAFT"
            meeting.save()
            messages.success(request, "جلسه ایجاد شد.")
            return redirect("meeting-detail", pk=meeting.id)

        return render(request, self.template_name, {"form": form})


@login_required
def add_invitee(request, meeting_id: int):
    meeting = get_object_or_404(Meeting, pk=meeting_id)

    # فقط creator یا secretary یا superuser
    if not (request.user.is_superuser or meeting.created_by_id == request.user.id or meeting.secretary_id == request.user.id):
        raise PermissionDenied("اجازه اضافه کردن مدعو را ندارید.")

    if request.method == "POST":
        # اگر InviteeAddForm را در meetings/forms.py ساخته باشی، استفاده می‌کنیم؛ وگرنه fallback
        try:
            form = InviteeAddForm(request.POST)
        except Exception:
            form = _InviteeAddFormFallback(request.POST)

        if form.is_valid():
            ident = form.cleaned_data["invitee_identifier"].strip()

            user = User.objects.filter(username=ident).first() or User.objects.filter(email=ident).first()
            if not user:
                messages.error(request, "کاربر پیدا نشد.")
                return redirect("meeting-detail", pk=meeting.id)

            inv, created = Invitation.objects.get_or_create(meeting=meeting, invitee=user)
            if created:
                messages.success(request, f"{user.username} به جلسه اضافه شد.")
            else:
                messages.info(request, "این کاربر قبلاً اضافه شده بود.")
        else:
            messages.error(request, "فرم معتبر نیست.")

    return redirect("meeting-detail", pk=meeting.id)
