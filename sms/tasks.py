import logging
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from requests import RequestException

from .models import OutboundSMS, SMSStatus
from .services import get_provider

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 5
BASE_BACKOFF = 60  # seconds
MAX_BACKOFF = 60 * 60  # 1 hour

def _is_transient(exc, provider_response: str) -> bool:
    if isinstance(exc, RequestException):
        return True
    if provider_response:
        lower = provider_response.lower()
        if any(k in lower for k in ("timeout", "tempor", "try again", "server error", "502", "503", "504")):
            return True
    return False

def _compute_backoff(attempts: int) -> int:
    backoff = BASE_BACKOFF * (2 ** max(0, attempts - 1))
    return min(backoff, MAX_BACKOFF)

@shared_task(bind=True, autoretry_for=(), retry_backoff=False)
def send_outbound_sms(self, sms_id: int):
    # 1) lock and increment attempts safely
    try:
        with transaction.atomic():
            sms = OutboundSMS.objects.select_for_update().get(id=sms_id)
            if sms.status == SMSStatus.SENT:
                logger.info("SMS %s already SENT", sms_id); return
            if sms.scheduled_at and sms.scheduled_at > timezone.now():
                delta = int((sms.scheduled_at - timezone.now()).total_seconds())
                logger.info("SMS %s scheduled in %s seconds", sms_id, delta)
                raise self.retry(countdown=max(1, delta))
            if sms.attempts >= MAX_ATTEMPTS:
                reason = f"max attempts reached ({sms.attempts})"
                logger.warning("SMS %s permanently failed: %s", sms_id, reason)
                sms.mark_failed(error=reason, provider_response=sms.provider_response or "")
                return
            sms.attempts += 1
            sms.status = SMSStatus.SENT
            sms.started_at = timezone.now()
            sms.save(update_fields=["attempts", "status", "started_at"])
    except OutboundSMS.DoesNotExist:
        logger.error("OutboundSMS %s not found", sms_id); return

    # 2) send (outside transaction)
    provider = get_provider()
    try:
        result = provider.send(sms.to, sms.body)
    except Exception as exc:
        provider_resp = str(exc)
        transient = _is_transient(exc, provider_resp)
        logger.exception("Exception sending SMS %s: %s", sms_id, exc)
        if transient and sms.attempts < MAX_ATTEMPTS:
            countdown = _compute_backoff(sms.attempts)
            with transaction.atomic():
                OutboundSMS.objects.filter(id=sms_id).update(provider_response=provider_resp)
            raise self.retry(exc=exc, countdown=countdown)
        with transaction.atomic():
            OutboundSMS.objects.filter(id=sms_id).update(status=SMSStatus.FAILED, error=provider_resp, provider_response=provider_resp)
        return

    # 3) parse result
    ok = getattr(result, "ok", False)
    provider_id = getattr(result, "provider_message_id", "") or ""
    provider_resp_raw = getattr(result, "response", "") or ""
    provider_err = getattr(result, "error", "") or ""

    if ok:
        try:
            with transaction.atomic():
                sms_ref = OutboundSMS.objects.select_for_update().get(id=sms_id)
                if sms_ref.status == SMSStatus.SENT:
                    logger.info("SMS %s already marked sent", sms_id); return
                sms_ref.mark_sent(provider_message_id=provider_id, provider_response=provider_resp_raw)
            logger.info("SMS %s marked SENT", sms_id); return
        except Exception as exc:
            logger.exception("Failed to mark SMS %s as sent: %s", sms_id, exc)
            raise

    # not ok -> decide transient or permanent
    transient_flag = _is_transient(Exception(provider_err), provider_resp_raw)
    if transient_flag and sms.attempts < MAX_ATTEMPTS:
        countdown = _compute_backoff(sms.attempts)
        with transaction.atomic():
            OutboundSMS.objects.filter(id=sms_id).update(provider_response=provider_resp_raw)
        raise self.retry(exc=Exception(provider_err or "Provider temporary failure"), countdown=countdown)

    # permanent fail
    with transaction.atomic():
        OutboundSMS.objects.filter(id=sms_id).update(status=SMSStatus.FAILED, error=provider_err or "Provider returned failure", provider_response=provider_resp_raw)
    logger.error("SMS %s permanently failed: %s", sms_id, provider_resp_raw)
    return