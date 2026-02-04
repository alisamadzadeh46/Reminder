from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings

def send_meeting_invitation(invitation):
    meeting = invitation.meeting
    user = invitation.invitee

    subject = f"دعوتنامه جلسه: {meeting.title}"
    msg = (
        f"سلام {user.get_full_name() or user.username}\n\n"
        f"شما به جلسه زیر دعوت شده‌اید:\n"
        f"- عنوان: {meeting.title}\n"
        f"- زمان: {meeting.start_at:%Y-%m-%d %H:%M} تا {meeting.end_at:%H:%M}\n"
        f"- مکان/لینک: {meeting.location}\n\n"
        f"توضیحات:\n{meeting.description}\n"
    )
    send_mail(subject, msg, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)

    invitation.invited_at = timezone.now()
    invitation.save(update_fields=["invited_at"])
