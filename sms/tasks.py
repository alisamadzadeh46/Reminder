from celery import shared_task
from django.utils import timezone

from sms.models import OutboundSMS, SMSStatus
from .services import get_provider


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_outbound_sms(self, outbound_sms_id: int):
    sms = OutboundSMS.objects.filter(id=outbound_sms_id).first()
    if not sms:
        return

    if sms.status == SMSStatus.SENT:
        return


    if sms.scheduled_at and sms.scheduled_at > timezone.now():
        return

    sms.attempts += 1
    sms.save(update_fields=["attempts"])

    provider = get_provider()
    try:
        result = provider.send(sms.to, sms.body)
        if result.ok:
            sms.mark_sent(provider_message_id=result.provider_message_id or "", provider_response=result.response or "")
        else:
            sms.mark_failed(error=result.error or "Provider error", provider_response=result.response or "")
            raise Exception(result.error or "Provider error")
    except Exception as e:
        raise self.retry(exc=e)