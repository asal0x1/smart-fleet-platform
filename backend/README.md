# SMART FLEET — Backend (Django REST Framework)

Taksi, og'ir texnika va to'y transporti marketplace uchun to'liq backend.

## Texnologiyalar

- **Python 3.9** + Django 4.2 LTS
- Django REST Framework 3.15
- PostgreSQL + PostGIS (GeoDjango)
- SimpleJWT (access + refresh)
- drf-spectacular (Swagger UI)

## Struktura

```
smart_fleet/
├── config/
│   ├── settings/       # base / dev / prod
│   ├── urls.py
│   ├── wsgi.py / asgi.py
├── apps/
│   ├── common/         # base model, pagination, responses, permissions, admin stats
│   ├── users/          # User (phone=login), OTP, JWT auth
│   ├── drivers/        # haydovchi profili, lokatsiya, nearby (PostGIS)
│   ├── orders/         # buyurtma lifecycle, narx, tariflar
│   ├── payments/       # Click + webhook (prepare/complete)
│   └── requests/       # og'ir texnika + to'y so'rovlari
├── services/           # sms (Eskiz), map (Yandex/OSRM), payment (Click), email
├── requirements/
└── manage.py
```

## O'rnatish

**Python 3.9** kerak. PostGIS uchun PostgreSQL da `CREATE EXTENSION postgis;`.

> **Windows'da GDAL:** GeoDjango uchun eng oson yo'l — PostgreSQL + PostGIS
> installerini (yoki OSGeo4W) o'rnatish; u GDAL/GEOS ni ham beradi.

```bash
# 1. Virtual environment
python -m venv venv
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# 2. Paketlar
python -m pip install --upgrade pip
pip install -r requirements/dev.txt

# 3. Sozlash
cp .env.example .env      # Windows: copy .env.example .env
# .env ni tahrirlang

# 4. Migratsiya
python manage.py makemigrations
python manage.py migrate

# 5. Tariflarni yuklash
python manage.py seed_tariffs

# 6. Admin
python manage.py createsuperuser

# 7. Ishga tushirish
python manage.py runserver
```

## API hujjatlari (Swagger)

`http://localhost:8000/api/docs/`

## Endpointlar

### Auth (`/api/auth/`)
| Method | URL | Tavsif |
|--------|-----|--------|
| POST | `register/` | Ro'yxatdan o'tish |
| POST | `login/` | Kirish |
| POST | `send-otp/` | OTP yuborish |
| POST | `verify-otp/` | OTP tasdiqlash |
| POST | `refresh/` | Token yangilash |
| GET/PATCH | `profile/` | Profil |

### Drivers (`/api/drivers/`)
| Method | URL | Tavsif |
|--------|-----|--------|
| GET/PATCH | `profile/` | Haydovchi profili |
| POST | `location/` | Lokatsiya yangilash |
| POST | `online/` | Online/offline |
| GET | `nearby/?lat=&lng=&radius=` | Yaqin haydovchilar |

### Orders (`/api/orders/`)
| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `tariffs/` | Tariflar |
| POST | `estimate/` | Narxni oldindan hisoblash |
| GET/POST | `` | Buyurtmalar / yangi buyurtma |
| GET | `available/` | Ochiq buyurtmalar (haydovchi) |
| GET | `<id>/` | Buyurtma detali |
| PATCH | `<id>/status/` | Status o'zgartirish |

### Payments (`/api/payments/`)
| Method | URL | Tavsif |
|--------|-----|--------|
| POST | `create/` | To'lov boshlash (Click havolasi) |
| POST | `click/prepare/` | Click webhook (prepare) |
| POST | `click/complete/` | Click webhook (complete) |

### Requests
| Method | URL | Tavsif |
|--------|-----|--------|
| POST | `/api/heavy-equipment/requests/` | Og'ir texnika so'rovi |
| POST | `/api/wedding/requests/` | To'y transporti so'rovi |

### Admin
| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `/api/admin/stats/` | Dashboard statistikasi |

## Order status flow

```
pending -> accepted -> driver_arrived -> ongoing -> completed
   |          |             |               |
   +----------+-------------+---------------+--> cancelled
```

## Tashqi servislar

| Servis | Holat | Izoh |
|--------|-------|------|
| Eskiz SMS | **Mock** | Dev'da OTP konsolga chiqadi (`ESKIZ_MOCK=True`) |
| Yandex Maps | Real | `.env` da `YANDEX_MAPS_API_KEY` |
| OSRM | Real | Public server (kalitsiz). Xato bo'lsa haversine fallback |
| Click | Real | `.env` da kalitlar, webhook signature MD5 |
| Email | Console | Dev'da konsolga; prod'da SMTP |

## Holat

- [x] Kun 1: Loyiha asoslari, settings, common
- [x] Kun 2: Auth (User, OTP, JWT)
- [x] Kun 3: Orders + Tariffs + narx hisoblash + status flow
- [x] Kun 4: Drivers + Geolocation (PostGIS nearby)
- [x] Kun 7: Payments (Click prepare/complete) + Admin stats
- [x] Kun 8: Heavy equipment so'rovlari + email
- [x] Kun 9: Wedding so'rovlari + email
- [ ] Kun 10: Deploy (Docker/Nginx) — keyingi bosqich
