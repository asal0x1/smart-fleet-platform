"""So'rovlar uchun narx hisoblash."""
from django.conf import settings


def heavy_equipment_price(category, items, duration_days=1):
    """Og'ir texnika taxminiy narxi.

    Formula: sum(dona soni) * kunlik_narx * kunlar

    Kunlik narxlar `.env` orqali sozlanadi (HEAVY_RATE_EARTH va h.k.) —
    ilgari og'ir texnika uchun narx umuman hisoblanmasdi, operator har
    safar qo'lda aytardi.
    """
    dona = 0
    for item in items or []:
        try:
            dona += int(item.get("quantity", 1))
        except (TypeError, ValueError):
            dona += 1
    dona = max(1, dona)

    kunlik = settings.HEAVY_EQUIPMENT_RATES.get(
        category, settings.HEAVY_EQUIPMENT_DEFAULT_RATE
    )
    kunlar = max(1, int(duration_days or 1))
    return dona * kunlik * kunlar


def wedding_price(car_count, duration_hours=1):
    """To'y transporti taxminiy narxi."""
    return (
        max(1, int(car_count or 1))
        * max(1, int(duration_hours or 1))
        * settings.WEDDING_HOURLY_RATE
    )


# Shartnoma muddati -> teng keladigan kunlar soni (narx hisoblash uchun)
PERSONAL_DRIVER_DURATION_DAYS = {
    "1_day": 1,
    "1_week": 7,
    "1_month": 30,
    "3_months": 90,
    "6_months": 180,
    "1_year": 365,
}


def personal_driver_price(contract_duration):
    """Shaxsiy haydovchi taxminiy narxi: kunlik narx * muddat (kun)."""
    kunlar = PERSONAL_DRIVER_DURATION_DAYS.get(contract_duration, 1)
    return kunlar * settings.PERSONAL_DRIVER_DAILY_RATE


def bus_price(bus_count, duration_hours=1):
    """Avtobus ijarasi taxminiy narxi."""
    return (
        max(1, int(bus_count or 1))
        * max(1, int(duration_hours or 1))
        * settings.BUS_HOURLY_RATE
    )


def gift_memorial_price(kind):
    """Hadiya/Maraka taxminiy bazaviy narxi."""
    if kind == "gift":
        return settings.GIFT_BASE_PRICE
    return settings.MEMORIAL_BASE_PRICE
