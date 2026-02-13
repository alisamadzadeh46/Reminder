import json
from dataclasses import dataclass
from typing import Optional

import requests
from requests import RequestException

from .models import SMSProviderSettings

@dataclass
class SMSResult:
    ok: bool
    provider_message_id: Optional[str] = None
    response: Optional[str] = None
    error: Optional[str] = None

class SMSProvider:
    def send(self, to: str, text: str) -> SMSResult:
        raise NotImplementedError

class FakeProvider(SMSProvider):
    def send(self, to: str, text: str) -> SMSResult:
        return SMSResult(ok=True, provider_message_id="FAKE-"+(to or "")[:8], response="FAKE_OK")

class PayamakVipProvider(SMSProvider):
    def __init__(self, base_url: str, username: str, password: str, from_number: str, is_flash: bool=False, send_delay: int=0):
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
            raw_text = r.text
            if r.status_code != 200:
                return SMSResult(ok=False, response=raw_text, error=f"HTTP {r.status_code}")
            try:
                js = r.json()
            except Exception:
                js = None

            ok = False
            provider_id = None
            err = None

            if isinstance(js, dict):
                # payamak.vip specific: Result == 0 means success
                if "Result" in js:
                    ok = js.get("Result") == 0
                    provider_id = js.get("BatchSmsId") or js.get("batchSmsId")
                    err = js.get("ErrorMessage") or js.get("Error") or None
                # fallback: other providers
                elif js.get("RetStatus") is not None:
                    ret = js.get("RetStatus")
                    ok = ret in (0, "0", 1, "1")
                    provider_id = js.get("SmsId") or js.get("BatchSmsId") or js.get("Id")
                    err = js.get("StrRetStatus") or js.get("Message") or None
                elif js.get("Success") is True or js.get("IsSuccessful") is True:
                    ok = True
                    provider_id = js.get("SmsId") or js.get("BatchSmsId") or js.get("Id")
                    err = js.get("Message") or None
                else:
                    ok = False
                    err = js.get("Message") or js.get("error") or None
            else:
                s = (raw_text or "").strip()
                if s.isdigit():
                    ok = True
                    provider_id = s
                else:
                    ok = False
                    err = raw_text

            return SMSResult(ok=ok, provider_message_id=str(provider_id) if provider_id else None,
                             response=json.dumps(js, ensure_ascii=False) if js is not None else raw_text,
                             error=err)
        except RequestException as e:
            return SMSResult(ok=False, response=str(e), error=str(e))
        except Exception as e:
            return SMSResult(ok=False, response=str(e), error=str(e))

def get_provider() -> SMSProvider:
    s = SMSProviderSettings.objects.first()
    if not s or not s.is_enabled:
        return FakeProvider()
    if s.provider == "PAYAMAKVIP":
        if not (s.username and s.password and s.from_number):
            return FakeProvider()
        return PayamakVipProvider(base_url=s.base_url, username=s.username, password=s.password,
                                 from_number=s.from_number, is_flash=s.is_flash, send_delay=s.send_delay)
    return FakeProvider()