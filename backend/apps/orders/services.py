"""Buyurtma biznes-logikasi (view'lardan ajratilgan)."""
from django.contrib.gis.geos import Point
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.notifications.services import (
    broadcast_new_order,
    notify_order_status,
)
from services.map import map_service

from .models import Order, OrderStatus, Tariff

# Ruxsat etilgan status o'tishlari
STATUS_FLOW = {
    OrderStatus.PENDING: [OrderStatus.ACCEPTED, OrderStatus.CANCELLED],
    OrderStatus.ACCEPTED: [OrderStatus.DRIVER_ARRIVED, OrderStatus.CANCELLED],
    OrderStatus.DRIVER_ARRIVED: [OrderStatus.ONGOING, OrderStatus.CANCELLED],
    OrderStatus.ONGOING: [OrderStatus.COMPLETED, OrderStatus.CANCELLED],
    OrderStatus.COMPLETED: [],
    OrderStatus.CANCELLED: [],
}


def estimate_order(tariff, from_lat, from_lng, to_lat, to_lng):
    """Narx va masofani hisoblaydi (order yaratmasdan)."""
    route = map_service.route(from_lat, from_lng, to_lat, to_lng)
    price = tariff.calculate_price(route["distance_km"], route["duration_min"])
    return {
        "estimated_price": price,
        "distance_km": route["distance_km"],
        "duration_min": route["duration_min"],
    }


def create_order(client, data):
    """Yangi buyurtma yaratadi (narxni avtomatik hisoblab)."""
    tariff = Tariff.objects.filter(id=data["tariff_id"], is_active=True).first()
    if tariff is None:
        raise ValidationError({"tariff_id": "Tarif topilmadi"})

    estimate = estimate_order(
        tariff,
        data["from_lat"], data["from_lng"],
        data["to_lat"], data["to_lng"],
    )

    order = Order.objects.create(
        client=client,
        tariff=tariff,
        from_address=data["from_address"],
        from_location=Point(data["from_lng"], data["from_lat"], srid=4326),
        to_address=data["to_address"],
        to_location=Point(data["to_lng"], data["to_lat"], srid=4326),
        payment_method=data.get("payment_method", "cash"),
        estimated_price=estimate["estimated_price"],
        distance_km=estimate["distance_km"],
        duration_min=estimate["duration_min"],
    )
    broadcast_new_order(order)
    return order


def change_status(order, new_status, driver=None, actual_distance_km=None):
    """Status o'zgartiradi (flow tekshiruvi bilan).

    `actual_distance_km` — haydovchi ilovasi o'lchagan haqiqiy masofa.
    Berilsa, yakuniy narx shu bo'yicha qayta hisoblanadi.
    """
    allowed = STATUS_FLOW.get(order.status, [])
    if new_status not in allowed:
        raise ValidationError(
            {"status": f"'{order.status}' -> '{new_status}' o'tish mumkin emas"}
        )

    now = timezone.now()

    if new_status == OrderStatus.ACCEPTED:
        if driver is None:
            raise ValidationError({"driver": "Haydovchi kerak"})
        order.driver = driver
        order.accepted_at = now

    elif new_status == OrderStatus.ONGOING:
        order.started_at = now

    elif new_status == OrderStatus.COMPLETED:
        order.completed_at = now
        order.final_price = _final_price(order, now, actual_distance_km)
        if order.driver:
            order.driver.total_trips += 1
            order.driver.save(update_fields=["total_trips"])

    order.status = new_status
    order.save()

    notify_order_status(order)
    return order


def _final_price(order, now, actual_distance_km=None):
    """Yakuniy narxni hisoblaydi.

    Ilgari har doim `estimated_price` ga teng edi — ya'ni haydovchi
    boshqa yo'ldan yursa ham narx o'zgarmasdi. Endi:
      - haqiqiy masofa berilsa, tarif bo'yicha qayta hisoblanadi
      - haqiqiy safar vaqti (started_at -> completed_at) hisobga olinadi
      - kelishilgan narxdan 3 barobar oshib ketmasligi kafolatlanadi
        (GPS xatosi mijozga zarar qilmasin)
    """
    if actual_distance_km is None or order.tariff_id is None:
        return order.estimated_price

    if order.started_at:
        daqiqa = max(1, round((now - order.started_at).total_seconds() / 60))
    else:
        daqiqa = order.duration_min or 1

    narx = order.tariff.calculate_price(actual_distance_km, daqiqa)

    order.distance_km = actual_distance_km
    order.duration_min = daqiqa

    if order.estimated_price:
        narx = min(narx, order.estimated_price * 3)
    return narx


def recalculate_driver_rating(driver):
    """Haydovchi reytingini uning barcha sharhlari bo'yicha qayta hisoblaydi.

    Sharh bo'lmasa 5.0 qoladi — yangi haydovchi past reyting bilan
    boshlamasligi uchun.
    """
    from django.db.models import Avg

    from .models import Review, ReviewKind

    natija = Review.objects.filter(
        order__driver=driver, kind=ReviewKind.CLIENT_TO_DRIVER
    ).aggregate(avg=Avg("rating"))

    driver.rating = round(natija["avg"], 1) if natija["avg"] is not None else 5.0
    driver.save(update_fields=["rating", "updated_at"])
    return driver.rating
