from .models import OutboundSMS, SMSTemplate, SMSStatus
from .tasks import send_outbound_sms

def render_template_body(template: SMSTemplate, context: dict) -> str:
    try:
        return template.body.format(**context)
    except Exception:
        return template.body

def queue_sms(to: str, body: str, user=None, template: SMSTemplate | None = None,
              idempotency_key: str = "", scheduled_at=None) -> OutboundSMS:
    if idempotency_key:
        existing = OutboundSMS.objects.filter(idempotency_key=idempotency_key).exclude(status=SMSStatus.FAILED).first()
        if existing: return existing
    sms = OutboundSMS.objects.create(to=to, body=body, user=user, template=template, idempotency_key=idempotency_key or "", scheduled_at=scheduled_at)
    send_outbound_sms.delay(sms.id)
    return sms