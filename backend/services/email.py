"""Operatorga email xabar yuborish servisi."""
import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.operator_email = settings.OPERATOR_EMAIL
        self.from_email = settings.DEFAULT_FROM_EMAIL

    def send_heavy_equipment_request(self, req):
        items = "\n".join(
            f"  - {it.get('name')}: {it.get('quantity')} ta" for it in req.items
        )
        subject = f"Yangi og'ir texnika so'rovi #{req.id}"
        body = (
            f"Yangi so'rov!\n\n"
            f"Kategoriya: {req.get_category_display()}\n"
            f"Manzil: {req.address}\n"
            f"Boshlanish: {req.start_date} {req.start_time or ''}\n"
            f"Muddat: {req.duration_days} kun\n"
            f"Aloqa: {req.contact_name} — {req.contact_phone}\n\n"
            f"Texnikalar:\n{items}\n\n"
            f"Izoh: {req.notes}"
        )
        return self._send(subject, body)

    def send_wedding_request(self, req):
        subject = f"Yangi to'y transporti so'rovi #{req.id}"
        body = (
            f"Yangi so'rov!\n\n"
            f"Mashina: {req.car_brand} x {req.car_count}\n"
            f"Bezak: {req.get_decoration_type_display() if req.decoration_type else '-'}\n"
            f"Manzil: {req.address}\n"
            f"Sana: {req.date} {req.time or ''}\n"
            f"Muddat: {req.duration_hours} soat\n"
            f"Aloqa: {req.contact_name} — {req.contact_phone}\n\n"
            f"Izoh: {req.notes}"
        )
        return self._send(subject, body)

    def send_personal_driver_request(self, req):
        subject = f"Yangi shaxsiy haydovchi so'rovi #{req.id}"
        body = (
            f"Yangi so'rov!\n\n"
            f"Mashina: {req.car_brand}\n"
            f"Haydovchi tajribasi: {req.get_driver_experience_display()}\n"
            f"Shartnoma muddati: {req.get_contract_duration_display()}\n"
            f"Manzil: {req.address}\n"
            f"Boshlanish sanasi: {req.start_date}\n"
            f"Aloqa: {req.contact_name} — {req.contact_phone}\n\n"
            f"Izoh: {req.notes}"
        )
        return self._send(subject, body)

    def send_bus_request(self, req):
        subject = f"Yangi avtobus so'rovi #{req.id}"
        body = (
            f"Yangi so'rov!\n\n"
            f"Toifa: {req.get_category_display()}\n"
            f"Avtobus: {req.bus_brand} x {req.bus_count}\n"
            f"Manzil: {req.address}\n"
            f"Sana: {req.date} {req.time or ''}\n"
            f"Muddat: {req.duration_hours} soat\n"
            f"Aloqa: {req.contact_name} — {req.contact_phone}\n\n"
            f"Izoh: {req.notes}"
        )
        return self._send(subject, body)

    def send_gift_memorial_request(self, req):
        subject = f"Yangi hadiya/maraka so'rovi #{req.id}"
        body = (
            f"Yangi so'rov!\n\n"
            f"Turi: {req.get_kind_display()}\n"
            f"Bezak: {req.get_decoration_type_display() if req.decoration_type else '-'}\n"
            f"Manzil: {req.address}\n"
            f"Sana: {req.date} {req.time or ''}\n"
            f"Aloqa: {req.contact_name} — {req.contact_phone}\n\n"
            f"Izoh: {req.notes}"
        )
        return self._send(subject, body)

    def _send(self, subject, body):
        try:
            send_mail(
                subject, body, self.from_email, [self.operator_email],
                fail_silently=False,
            )
            return True
        except Exception as exc:  # noqa
            logger.error("Email yuborish xatosi: %s", exc)
            return False


email_service = EmailService()
