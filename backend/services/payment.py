"""
Click Uzbekistan integratsiyasi.

To'lov oqimi:
  1. create_payment_url() — foydalanuvchiga to'lov havolasi
  2. Click webhook yuboradi -> Prepare (action=0)
  3. Click webhook yuboradi -> Complete (action=1)

Signature MD5 bilan tekshiriladi.
"""
import hashlib
import ipaddress

from django.conf import settings

# Click yuborgan summa bilan bizdagi summa orasidagi ruxsat etilgan farq (so'm).
# Click ba'zan "25000.00" ko'rinishida float yuboradi.
AMOUNT_TOLERANCE = 0.01


class ClickService:
    def __init__(self):
        self.service_id = settings.CLICK_SERVICE_ID
        self.merchant_id = settings.CLICK_MERCHANT_ID
        self.secret_key = settings.CLICK_SECRET_KEY

    def create_payment_url(self, order_id, amount):
        """Foydalanuvchi ochadigan to'lov havolasi."""
        return (
            "https://my.click.uz/services/pay"
            f"?service_id={self.service_id}"
            f"&merchant_id={self.merchant_id}"
            f"&amount={amount}"
            f"&transaction_param={order_id}"
        )

    def check_prepare_signature(self, data):
        """Prepare bosqichi imzosini tekshiradi."""
        raw = (
            f"{data.get('click_trans_id')}"
            f"{data.get('service_id')}"
            f"{self.secret_key}"
            f"{data.get('merchant_trans_id')}"
            f"{data.get('amount')}"
            f"{data.get('action')}"
            f"{data.get('sign_time')}"
        )
        return self._md5(raw) == data.get("sign_string")

    def check_complete_signature(self, data):
        """Complete bosqichi imzosini tekshiradi."""
        raw = (
            f"{data.get('click_trans_id')}"
            f"{data.get('service_id')}"
            f"{self.secret_key}"
            f"{data.get('merchant_trans_id')}"
            f"{data.get('merchant_prepare_id')}"
            f"{data.get('amount')}"
            f"{data.get('action')}"
            f"{data.get('sign_time')}"
        )
        return self._md5(raw) == data.get("sign_string")

    @staticmethod
    def check_amount(received, expected):
        """Click yuborgan summa bizdagi summaga mos kelishini tekshiradi.

        BU JUDA MUHIM: imzo faqat so'rov o'zgartirilmaganini isbotlaydi,
        summaning TO'G'RILIGINI emas. Tekshirilmasa, hujumchi o'z Click
        kabinetidan 1000 so'mlik to'lov yaratib, 500 000 so'mlik buyurtmani
        "to'langan" holatiga o'tkazishi mumkin.
        """
        try:
            received = float(received)
        except (TypeError, ValueError):
            return False
        return abs(received - float(expected)) <= AMOUNT_TOLERANCE

    @staticmethod
    def is_allowed_ip(ip):
        """Webhook Click serverlaridan kelganini tekshiradi.

        CLICK_ALLOWED_IPS bo'sh bo'lsa tekshiruv o'tkazib yuboriladi
        (dev/test uchun). Prod'da .env ga Click bergan IP'larni yozing.
        """
        allowed = getattr(settings, "CLICK_ALLOWED_IPS", [])
        if not allowed:
            return True
        if not ip:
            return False
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return False
        for entry in allowed:
            entry = entry.strip()
            if not entry:
                continue
            try:
                if "/" in entry:
                    if addr in ipaddress.ip_network(entry, strict=False):
                        return True
                elif addr == ipaddress.ip_address(entry):
                    return True
            except ValueError:
                continue
        return False

    @staticmethod
    def _md5(text):
        return hashlib.md5(text.encode()).hexdigest()


click_service = ClickService()


# Click webhook javob kodlari
CLICK_SUCCESS = 0
CLICK_SIGN_ERROR = -1
CLICK_INVALID_AMOUNT = -2
CLICK_ACTION_NOT_FOUND = -3
CLICK_ALREADY_PAID = -4
CLICK_ORDER_NOT_FOUND = -5
CLICK_TRANSACTION_NOT_FOUND = -6
CLICK_TRANSACTION_CANCELLED = -9
