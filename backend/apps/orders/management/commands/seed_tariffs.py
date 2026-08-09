"""Boshlang'ich tariflarni yaratish uchun management command.

Ishlatish: python manage.py seed_tariffs
"""
from django.core.management.base import BaseCommand

from apps.orders.models import Tariff

TARIFFS = [
    {"name": "Standard", "name_uz": "Standart", "base_fare": 5000, "per_km": 1500, "per_minute": 300, "minimum_fare": 8000},
    {"name": "Comfort", "name_uz": "Komfort", "base_fare": 7000, "per_km": 2000, "per_minute": 400, "minimum_fare": 12000},
    {"name": "Business", "name_uz": "Biznes", "base_fare": 10000, "per_km": 3000, "per_minute": 600, "minimum_fare": 20000},
    {"name": "Premium", "name_uz": "Premium", "base_fare": 15000, "per_km": 5000, "per_minute": 1000, "minimum_fare": 35000},
]


class Command(BaseCommand):
    help = "Boshlang'ich tariflarni yaratadi"

    def handle(self, *args, **options):
        created = 0
        for data in TARIFFS:
            obj, is_new = Tariff.objects.get_or_create(
                name=data["name"], defaults=data
            )
            if is_new:
                created += 1
        self.stdout.write(
            self.style.SUCCESS(f"{created} ta yangi tarif yaratildi (jami: {Tariff.objects.count()})")
        )
