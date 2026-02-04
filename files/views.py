from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect

from .forms import AttachmentForm
from meetings.models import Meeting
from tasks.models import Task


def _can_attach_to_meeting(user, meeting: Meeting) -> bool:
    if user.is_superuser:
        return True
    return meeting.created_by_id == user.id or meeting.secretary_id == user.id or meeting.follow_up_owner_id == user.id


def _can_attach_to_task(user, task: Task) -> bool:
    if user.is_superuser:
        return True
    if task.created_by_id == user.id or task.assignee_id == user.id or (task.follower_id == user.id):
        return True
    if task.meeting_id and task.meeting.follow_up_owner_id == user.id:
        return True
    return False


@login_required
def upload_meeting_attachment(request, meeting_id: int):
    meeting = get_object_or_404(Meeting, pk=meeting_id)
    if not _can_attach_to_meeting(request.user, meeting):
        raise PermissionDenied("اجازه پیوست فایل به این جلسه را ندارید.")

    if request.method == "POST":
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            att = form.save(commit=False)
            att.uploaded_by = request.user
            att.content_type = ContentType.objects.get_for_model(Meeting)
            att.object_id = meeting.id
            att.save()
            messages.success(request, "فایل پیوست شد.")
        else:
            messages.error(request, "فرم پیوست معتبر نیست.")

    return redirect("meeting-detail", pk=meeting.id)


@login_required
def upload_task_attachment(request, task_id: int):
    task = get_object_or_404(Task, pk=task_id)
    if not _can_attach_to_task(request.user, task):
        raise PermissionDenied("اجازه پیوست فایل به این وظیفه را ندارید.")

    if request.method == "POST":
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            att = form.save(commit=False)
            att.uploaded_by = request.user
            att.content_type = ContentType.objects.get_for_model(Task)
            att.object_id = task.id
            att.save()
            messages.success(request, "فایل پیوست شد.")
        else:
            messages.error(request, "فرم پیوست معتبر نیست.")

    return redirect("my-tasks")
