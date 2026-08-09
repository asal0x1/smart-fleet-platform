"""
Eskiz.uz SMS servisi.

ESKIZ_MOCK=True bo'lsa — SMS yubormaydi, konsolga chiqaradi (dev).
ESKIZ_MOCK=False bo'lsa — haqiqiy Eskiz API ga so'rov yuboradi.
"""
import logging

import requests
from django.conf import settings
from django.core.cache import cache

#: Eskiz tokeni 30 kun amal qiladi, biz 29 kun keshlaymiz
TOKEN_CACHE_KEY = "eskiz:token"
TOKEN_TTL = 29 * 24 * 60 * 60

logger = logging.getLogger(__name__)


class EskizSMSService:
    def __init__(self):
        self.mock = settings.ESKIZ_MOCK
        self.base_url = settings.ESKIZ_BASE_URL
        self.email = settings.ESKIZ_EMAIL
        self.password = settings.ESKIZ_PASSWORD

    # --- Public API ---

    def send_otp(self, phone, code):
        """OTP kodini yuboradi. (message_id, ok) qaytaradi."""
        text = f"SMART FLEET tasdiqlash kodi: {code}"
        return self.send(phone, text)

    def send(self, phone, text):
        if self.mock:
            logger.info("[MOCK SMS] -> %s: %s", phone, text)
            print(f"\n[MOCK SMS] -> {phone}: {text}\n")
            return {"message_id": "mock-0000", "ok": True}
        return self._send_real(phone, text)

    # --- Real Eskiz integration ---

    def _get_token(self, force_refresh=False):
        """Tokenni cache'dan oladi, bo'lmasa Eskiz'dan so'raydi.

        Ilgari token `self._token` da — ya'ni bitta jarayon xotirasida —
        saqlanardi. Bir nechta gunicorn worker'da har biri alohida login
        qilardi va muddati tugagach hech qachon yangilanmasdi.
        """
        if not force_refresh:
            token = cache.get(TOKEN_CACHE_KEY)
            if token:
                return token

        resp = requests.post(
            f"{self.base_url}/auth/login",
            data={"email": self.email, "password": self.password},
            timeout=10,
        )
        resp.raise_for_status()
        token = resp.json()["data"]["token"]
        cache.set(TOKEN_CACHE_KEY, token, TOKEN_TTL)
        return token

    def _post_sms(self, token, phone, text):
        return requests.post(
            f"{self.base_url}/message/sms/send",
            headers={"Authorization": f"Bearer {token}"},
            data={
                "mobile_phone": phone.lstrip("+"),
                "message": text,
                "from": "4546",
            },
            timeout=10,
        )

    def _send_real(self, phone, text):
        try:
            resp = self._post_sms(self._get_token(), phone, text)

            # Token eskirgan bo'lsa bir marta yangilab qayta urinamiz
            if resp.status_code in (401, 403):
                cache.delete(TOKEN_CACHE_KEY)
                resp = self._post_sms(
                    self._get_token(force_refresh=True), phone, text
                )

            resp.raise_for_status()
            data = resp.json()
            return {"message_id": data.get("id", ""), "ok": True}
        except requests.RequestException as exc:
            logger.error("Eskiz SMS xatosi: %s", exc)
            return {"message_id": "", "ok": False}


sms_service = EskizSMSService()
