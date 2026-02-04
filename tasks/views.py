from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import TaskCreateForm
from .models import Task


class TaskFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "جستجو در عنوان یا توضیحات..."
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[("", "همه وضعیت‌ها")] + Task.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    due = forms.ChoiceField(
        required=False,
        choices=[
            ("", "همه سررسیدها"),
            ("today", "امروز"),
            ("7d", "۷ روز آینده"),
            ("48h", "۴۸ ساعت آینده"),
            ("overdue", "عقب‌افتاده"),
            ("nodue", "بدون سررسید"),
        ],
        widget=forms.Select(attrs={"class": "form-select"})
    )


class TaskStatusForm(forms.Form):
    status = forms.ChoiceField(
        choices=Task.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"})
    )


def can_set_status(user, task: Task, status: str) -> bool:
    """
    قوانین تغییر وضعیت:
    - superuser: همه
    - INPROGRESS: assignee یا created_by
    - DONE: فقط assignee
    - VERIFIED: follower یا follow_up_owner جلسه
    - APPROVED/REJECTED: approver یا approver جلسه
    """
    if user.is_superuser:
        return True

    if status == "INPROGRESS":
        return task.assignee_id == user.id or task.created_by_id == user.id

    if status == "DONE":
        return task.assignee_id == user.id

    if status == "VERIFIED":
        return task.follower_id == user.id or (task.meeting_id and task.meeting.follow_up_owner_id == user.id)

    if status in ("APPROVED", "REJECTED"):
        return task.approver_id == user.id or (task.meeting_id and task.meeting.approver_id == user.id)

    # OPEN یا سایر حالت‌ها را از UI تغییر نمی‌دیم مگر superuser
    return False


@login_required
def my_tasks(request):
    u = request.user
    now = timezone.now()

    # base queryset
    qs = (
        Task.objects.filter(
            Q(assignee=u) | Q(created_by=u) | Q(follower=u) | Q(approver=u)
        )
        .distinct()
        .select_related("meeting", "assignee", "created_by")
        .order_by("-created_at")
    )

    # apply filters
    filter_form = TaskFilterForm(request.GET or None)
    if filter_form.is_valid():
        q = (filter_form.cleaned_data.get("q") or "").strip()
        status = filter_form.cleaned_data.get("status") or ""
        due = filter_form.cleaned_data.get("due") or ""

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

        if status:
            qs = qs.filter(status=status)

        if due == "today":
            qs = qs.filter(due_date__date=now.date())

        elif due == "7d":
            qs = qs.filter(due_date__gte=now, due_date__lte=now + timezone.timedelta(days=7))

        elif due == "48h":
            qs = qs.filter(due_date__gte=now, due_date__lte=now + timezone.timedelta(hours=48))

        elif due == "overdue":
            qs = qs.filter(due_date__isnull=False, due_date__lt=now).exclude(
                status__in=["DONE", "VERIFIED", "APPROVED", "REJECTED"]
            )

        elif due == "nodue":
            qs = qs.filter(due_date__isnull=True)

    # KPI
    total = qs.count()
    open_count = qs.exclude(status__in=["APPROVED", "REJECTED"]).count()
    due_48h = qs.filter(
        due_date__isnull=False,
        due_date__gte=now,
        due_date__lte=now + timezone.timedelta(hours=48),
    ).exclude(status__in=["DONE", "VERIFIED", "APPROVED", "REJECTED"]).count()
    overdue = qs.filter(
        due_date__isnull=False,
        due_date__lt=now,
    ).exclude(status__in=["DONE", "VERIFIED", "APPROVED", "REJECTED"]).count()

    # pagination
    paginator = Paginator(qs, 15)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)

    # allowed statuses per task (dict)
    allowed_map = {}
    for t in page_obj.object_list:
        allowed_map[t.id] = [s for s, _ in Task.STATUS_CHOICES if can_set_status(u, t, s)]

    return render(request, "tasks/my_tasks.html", {
        "filter_form": filter_form,
        "page_obj": page_obj,
        "kpi": {"total": total, "open": open_count, "due_48h": due_48h, "overdue": overdue},
        "allowed_map": allowed_map,
        "now": now,
    })


@login_required
def task_change_status(request, pk: int):
    task = get_object_or_404(Task, pk=pk)
    u = request.user

    if request.method != "POST":
        return redirect("my-tasks")

    form = TaskStatusForm(request.POST)
    if not form.is_valid():
        messages.error(request, "فرم معتبر نیست.")
        return redirect("my-tasks")

    new_status = form.cleaned_data["status"]

    if not can_set_status(u, task, new_status):
        raise PermissionDenied("اجازه تغییر وضعیت به این حالت را ندارید.")

    task.status = new_status
    task.save(update_fields=["status"])
    messages.success(request, "وضعیت وظیفه تغییر کرد.")

    # برگشت به همان صفحه با querystring
    next_url = request.POST.get("next") or ""
    if next_url.startswith("/"):
        return redirect(next_url)
    return redirect("my-tasks")


def _can_create_task(user):
    return user.is_superuser or user.is_staff


@login_required
def task_create(request):
    if not _can_create_task(request.user):
        raise PermissionDenied("اجازه ایجاد وظیفه ندارید.")

    if request.method == "POST":
        form = TaskCreateForm(request.POST)
        if form.is_valid():
            t = form.save(commit=False)
            t.created_by = request.user
            t.save()
            messages.success(request, "وظیفه ایجاد شد.")
            return redirect("my-tasks")
        messages.error(request, "فرم ایجاد وظیفه معتبر نیست.")
    else:
        form = TaskCreateForm()

    return render(request, "tasks/task_create.html", {"form": form})