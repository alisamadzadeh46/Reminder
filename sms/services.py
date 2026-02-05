import requests
from dataclasses import dataclass

from sms.models import SMSProviderSettings


@dataclass
class SMSResult:
    ok: bool
    provider_message_id: str | None = None
    response: str | None = None
    error: str | None = None


class SMSProvider:
    def send(self, to: str, text: str) -> SMSResult:
        raise NotImplementedError


class FakeProvider(SMSProvider):
    def send(self, to: str, text: str) -> SMSResult:
        return SMSResult(ok=True, provider_message_id="fake-1", response="FAKE_OK")


class PayamakVipProvider(SMSProvider):
    def __init__(self, base_url: str, username: str, password: str, from_number: str, is_flash: bool, send_delay: int):
        self.base_url = (base_url or "").rstrip("/") + "/"
        self.username = username
        self.password = password
        self.from_number = from_number
        self.is_flash = bool(is_flash)
        self.send_delay = int(send_delay or 0)

    def send(self, to: str, text: str) -> SMSResult:
        url = self.base_url + "SendBatchSms"
        payload = {
            "userName": self.username,
            "password": self.password,
            "fromNumber": self.from_number,
            "toNumbers": to,
            "messageContent": text,
            "isFlash": self.is_flash,
            "sendDelay": self.send_delay,
        }

        try:
            r = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=20)
            raw = r.text

            # بعضی سرویس‌ها JSON میدن، بعضی string. ما هر دو رو پوشش می‌دیم.
            if r.status_code != 200:
                return SMSResult(ok=False, error=f"HTTP {r.status_code}", response=raw)

            try:
                js = r.json()
            except Exception:
                js = None

            # تلاش برای تشخیص موفقیت بدون وابستگی به ساختار دقیق پاسخ
            provider_id = None
            ok = False
            err = None

            if isinstance(js, dict):
                # حالت‌های رایج:
                # RetStatus / Status / IsSuccessful / Success
                if js.get("RetStatus") in (1, True) or js.get("Status") in (1, True) or js.get("Success") is True or js.get("IsSuccessful") is True:
                    ok = True
                # id محتمل
                provider_id = js.get("SmsId") or js.get("smsId") or js.get("BatchSmsId") or js.get("batchSmsId") or js.get("Id") or js.get("id")
                # خطا محتمل
                err = js.get("StrRetStatus") or js.get("Message") or js.get("message") or js.get("Error") or js.get("error")
                # اگر کد وضعیت منفی/صفر باشد
                if js.get("RetStatus") in (0, -1, False) or js.get("Status") in (0, -1, False):
                    ok = False

            else:
                # اگر پاسخ فقط متن باشد، فرض می‌کنیم اگر عدد/شناسه برگشت، موفق است
                s = (raw or "").strip()
                if s.isdigit():
                    ok = True
                    provider_id = s
                else:
                    ok = False
                    err = raw

            if ok:
                return SMSResult(ok=True, provider_message_id=str(provider_id or ""), response=raw)
            return SMSResult(ok=False, error=err or "Provider returned failure", response=raw)

        except Exception as e:
            return SMSResult(ok=False, error=str(e), response="")


def get_provider() -> SMSProvider:
    s = SMSProviderSettings.objects.first()
    if not s or not s.is_enabled:
        return FakeProvider()

    if s.provider == "PAYAMAKVIP":
        # اگر تنظیمات ناقص بود، Fail کنیم تا در Outbox مشخص شود
        if not s.username or not s.password or not s.from_number:
            return FakeProvider()
        return PayamakVipProvider(
            base_url=s.base_url,
            username=s.username,
            password=s.password,
            from_number=s.from_number,
            is_flash=s.is_flash,
            send_delay=s.send_delay,
        )

    return FakeProvider()