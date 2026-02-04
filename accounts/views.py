from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect
import json
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.db.models.functions import TruncDate
from django.shortcuts import render
from django.utils import timezone

from meetings.models import Meeting
from tasks.models import Task
from notifications.models import Notification




class RegisterForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = "form-control"
            field.widget.attrs.update({"class": css})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "ثبت‌نام با موفقیت انجام شد.")
            return redirect("dashboard")
        messages.error(request, "فرم ثبت‌نام معتبر نیست.")
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "خوش آمدید.")
            return redirect("dashboard")
        messages.error(request, "نام کاربری یا رمز عبور اشتباه است.")
    else:
        form = AuthenticationForm(request)

    return render(request, "accounts/login.html", {"form": form})


@login_required
def logout_confirm_view(request):

    return render(request, "accounts/logout.html")

@login_required
def dashboard(request):
    u = request.user
    now = timezone.now()

    # جلسات مرتبط با کاربر
    base_meetings = (
        Meeting.objects.filter(
            Q(created_by=u) |
            Q(secretary=u) |
            Q(follow_up_owner=u) |
            Q(approver=u) |
            Q(invitations__invitee=u)
        )
        .distinct()
    )

    meetings_today = base_meetings.filter(start_at__date=now.date()).order_by("start_at")

    # KPI ها
    unread_notifs = Notification.objects.filter(user=u, is_read=False).count()

    open_tasks = Task.objects.filter(assignee=u).exclude(
        status__in=["DONE", "VERIFIED", "APPROVED", "REJECTED"]
    ).count()

    due_48h = Task.objects.filter(
        assignee=u,
        due_date__isnull=False,
        due_date__gte=now,
        due_date__lte=now + timezone.timedelta(hours=48),
    ).exclude(status__in=["DONE", "VERIFIED", "APPROVED", "REJECTED"]).count()

    # نمودار ۷ روز آینده (تعداد جلسات در هر روز)
    start = now.date()
    end = (now + timezone.timedelta(days=6)).date()

    chart_qs = (
        base_meetings.filter(start_at__date__gte=start, start_at__date__lte=end)
        .annotate(d=TruncDate("start_at"))
        .values("d")
        .annotate(c=Count("id"))
        .order_by("d")
    )

    counts_map = {row["d"]: row["c"] for row in chart_qs}

    labels = []
    data = []
    for i in range(7):
        d = start + timezone.timedelta(days=i)
        labels.append(d.strftime("%Y-%m-%d"))
        data.append(int(counts_map.get(d, 0)))

    return render(request, "accounts/dashboard.html", {
        "meetings_today": meetings_today,
        "kpi": {
            "unread_notifs": unread_notifs,
            "open_tasks": open_tasks,
            "due_48h": due_48h,
            "today_meetings": meetings_today.count(),
        },
        "chart_labels": json.dumps(labels, ensure_ascii=False),
        "chart_data": json.dumps(data),
    })


def custom_permission_denied_view(request, exception):
    return render(request, "403.html", {"message": str(exception)}, status=403)