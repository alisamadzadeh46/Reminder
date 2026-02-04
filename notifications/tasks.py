from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from meetings.models import Meeting
from tasks.models import Task
from .models import ReminderLog


def _send_email(to_email: str, subject: str, body: str):
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)


@shared_task
def send_meeting_reminders():
    now = timezone.now()

    windows = [
        ("MEETING_24H", now + timezone.timedelta(hours=24), now + timezone.timedelta(hours=24, minutes=5)),
        ("MEETING_1H",  now + timezone.timedelta(hours=1),  now + timezone.timedelta(hours=1, minutes=5)),
    ]

    for rem_type, start, end in windows:
        meetings = Meeting.objects.filter(status="SCHEDULED", start_at__gte=start, start_at__lt=end)

        for m in meetings:
            if ReminderLog.objects.filter(reminder_type=rem_type, content_type="meeting", object_id=m.id).exists():
                continue

            invs = m.invitations.select_related("invitee").filter(reminder_enabled=True)
            for inv in invs:
                u = inv.invitee
                if not u.email:
                    continue
                subject = f"یادآوری جلسه: {m.title}"
                body = (
                    f"سلام {u.get_full_name() or u.username}\n\n"
                    f"یادآوری جلسه:\n"
                    f"- عنوان: {m.title}\n"
                    f"- زمان: {m.start_at:%Y-%m-%d %H:%M}\n"
                    f"- مکان/لینک: {m.location}\n"
                )
                _send_email(u.email, subject, body)

            ReminderLog.objects.create(reminder_type=rem_type, content_type="meeting", object_id=m.id)


@shared_task
def send_task_reminders():
    now = timezone.now()

    # 24 ساعت قبل سررسید
    due_start = now + timezone.timedelta(hours=24)
    due_end = now + timezone.timedelta(hours=24, minutes=5)

    tasks_24h = Task.objects.filter(due_date__gte=due_start, due_date__lt=due_end).exclude(
        status__in=["APPROVED", "REJECTED"]
    )

    for t in tasks_24h:
        if ReminderLog.objects.filter(reminder_type="TASK_24H", content_type="task", object_id=t.id).exists():
            continue
        if t.assignee.email:
            subject = f"یادآوری وظیفه: {t.title}"
            body = (
                f"سلام {t.assignee.get_full_name() or t.assignee.username}\n\n"
                f"وظیفه شما تا 24 ساعت دیگر سررسید می‌شود:\n"
                f"- عنوان: {t.title}\n"
                f"- سررسید: {t.due_date:%Y-%m-%d %H:%M}\n"
            )
            _send_email(t.assignee.email, subject, body)
        ReminderLog.objects.create(reminder_type="TASK_24H", content_type="task", object_id=t.id)

    # هشدار یک‌باره overdue
    overdue = Task.objects.filter(due_date__lt=now).exclude(status__in=["DONE", "VERIFIED", "APPROVED", "REJECTED"])
    for t in overdue:
        if ReminderLog.objects.filter(reminder_type="TASK_OVERDUE", content_type="task", object_id=t.id).exists():
            continue
        if t.assignee.email:
            subject = f"هشدار: وظیفه عقب‌افتاده است: {t.title}"
            body = (
                f"سلام {t.assignee.get_full_name() or t.assignee.username}\n\n"
                f"این وظیفه از سررسید گذشته:\n"
                f"- عنوان: {t.title}\n"
                f"- سررسید: {t.due_date:%Y-%m-%d %H:%M}\n"
            )
            _send_email(t.assignee.email, subject, body)
        ReminderLog.objects.create(reminder_type="TASK_OVERDUE", content_type="task", object_id=t.id)
