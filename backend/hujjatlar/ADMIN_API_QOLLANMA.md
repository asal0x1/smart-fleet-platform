# SMART FLEET — Admin API (frontend uchun)

TODO faylidagi "Admin API'da yetishmayotgan endpointlar" bo'limi to'liq yozildi.
**22 ta endpoint**, hammasi real PostGIS bazada sinovdan o'tkazilgan (45/45 test OK).

---

## 1. O'rnatish — 4 qadam

### 1-qadam: fayllarni ko'chirish

```
apps/common/admin_api/__init__.py       ← yangi
apps/common/admin_api/serializers.py    ← yangi
apps/common/admin_api/filters.py        ← yangi
apps/common/admin_api/views.py          ← yangi
apps/common/admin_api/urls.py           ← yangi
apps/common/admin_views.py              ← almashtiriladi (eski importlar sinmasligi uchun shim)
config/urls.py                          ← almashtiriladi
apps/orders/migrations/0003_order_cancel_reason.py  ← yangi
```

### 2-qadam: `apps/orders/models.py` ga bitta maydon qo'shish

`Order` klassi ichida, `accepted_at` dan **oldin**:

```python
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING
    )

    # ↓ SHU QATORNI QO'SHING
    cancel_reason = models.TextField("Bekor qilish sababi", blank=True, default="")

    accepted_at = models.DateTimeField(null=True, blank=True)
```

TODO'dagi *"Bekor qilish sababi (`cancel_reason`) saqlanmaydi"* punkti shu bilan yopiladi.

### 3-qadam: migratsiya

```bash
python manage.py migrate
```

(0003 migratsiyasi tayyor holda berilgan — `makemigrations` shart emas.)

### 4-qadam: tekshirish

```bash
python manage.py check
python manage.py runserver
```

Swagger: `http://localhost:8000/api/docs/` — barcha `/api/admin/...` endpointlari
request/response sxemasi bilan chiqadi.

> ⚠️ `config/urls.py` da `from apps.common.admin_views import DashboardStatsView`
> importi olib tashlandi, o'rniga `path("admin/", include("apps.common.admin_api.urls"))`
> qo'shildi. `GET /api/admin/stats/` eski manzilida ishlayveradi — frontend sinmaydi.

---

## 2. Endpointlar

Barchasi `Authorization: Bearer <access_token>` talab qiladi va
`IsAdminRole` bilan himoyalangan (`role="admin"` **yoki** `is_staff=True`).
Boshqa rol → `403`, token yo'q → `401`.

### Statistika

| Method | URL | Tavsif |
|---|---|---|
| GET | `/api/admin/stats/` | Dashboard: users / drivers / orders / revenue / requests bloklari |
| GET | `/api/admin/stats/revenue/` | `?from=&to=&group_by=day\|week\|month` — grafik uchun qator |

### Foydalanuvchilar

| Method | URL | Tavsif |
|---|---|---|
| GET | `/api/admin/users/` | Ro'yxat + filtr + qidiruv + pagination |
| GET | `/api/admin/users/{id}/` | Detal + oxirgi 10 buyurtma |
| PATCH | `/api/admin/users/{id}/block/` | `{"is_active": false}` |

Filtrlar: `role`, `is_active`, `is_verified`, `is_staff`, `created_from`, `created_to`
Qidiruv (`?search=`): telefon, F.I.O, email
Tartiblash (`?ordering=`): `created_at`, `full_name`, `last_login` (minus bilan teskari)

### Haydovchilar

| Method | URL | Tavsif |
|---|---|---|
| GET | `/api/admin/drivers/` | Ro'yxat |
| GET | `/api/admin/drivers/{id}/` | Detal + daromad + oxirgi 10 buyurtma |
| PATCH | `/api/admin/drivers/{id}/` | Mashina ma'lumotlarini tahrirlash |
| PATCH | `/api/admin/drivers/{id}/approve/` | **Tasdiqlash** (`Driver.is_active`) |
| PATCH | `/api/admin/drivers/{id}/block/` | **Bloklash** (`User.is_active` — login qila olmaydi) |

Filtrlar: `is_active`, `is_online`, `rating_min`, `has_location`, `created_from/to`
Qidiruv: telefon, F.I.O, `car_number`, `car_model`

> **approve va block farqi:**
> `approve` → haydovchi buyurtma olishga ruxsat oladi (hujjat tekshiruvi).
> `block` → hisob butunlay o'chadi, tizimga kira olmaydi.
> `approve` mashina raqami bo'sh bo'lsa `400` qaytaradi va tasdiq bekor qilinsa
> haydovchi avtomatik `is_online=False` ga o'tadi.

### Buyurtmalar

| Method | URL | Tavsif |
|---|---|---|
| GET | `/api/admin/orders/` | Ro'yxat |
| GET | `/api/admin/orders/{id}/` | Detal + to'lovlar tarixi |
| PATCH | `/api/admin/orders/{id}/cancel/` | `{"reason": "..."}` |
| PATCH | `/api/admin/orders/{id}/assign/` | `{"driver_id": 5}` — operator qo'lda biriktiradi |

Filtrlar: `status`, `payment_status`, `payment_method`, `client_id`, `driver_id`,
`tariff_id`, `no_driver`, `price_min`, `price_max`, `created_from`, `created_to`

`cancel` `STATUS_FLOW` ni hurmat qiladi — `completed`/`cancelled` buyurtma `400` beradi.
Bekor qilinganda kutilayotgan `Payment`lar avtomatik `cancelled` ga o'tadi.

### Tariflar (to'liq CRUD)

| Method | URL |
|---|---|
| GET / POST | `/api/admin/tariffs/` |
| GET / PATCH / DELETE | `/api/admin/tariffs/{id}/` |

`Order.tariff` da `on_delete=PROTECT` bo'lgani uchun **buyurtmasi bor tarif o'chirilmaydi** —
o'rniga `is_active=False` qilinadi va javobda shu haqda xabar keladi (500 xato o'rniga).
Validatsiya: `minimum_fare >= base_fare`.

### To'lovlar

| Method | URL |
|---|---|
| GET | `/api/admin/payments/` |

Filtrlar: `status`, `method`, `order_id`, `amount_min`, `amount_max`, `created_from/to`
Javobning `data` ichida qo'shimcha `summary` bor: `{"paid_amount": .., "total_amount": ..}` —
filtrga mos yig'indi (faqat joriy sahifa emas, **butun natija bo'yicha**).

### So'rovlar — og'ir texnika va to'y

| Method | URL |
|---|---|
| GET | `/api/admin/requests/heavy/` |
| GET / PATCH / DELETE | `/api/admin/requests/heavy/{id}/` |
| PATCH | `/api/admin/requests/heavy/{id}/status/` |
| GET | `/api/admin/requests/wedding/` |
| GET / PATCH / DELETE | `/api/admin/requests/wedding/{id}/` |
| PATCH | `/api/admin/requests/wedding/{id}/status/` |

Status: `pending` → `contacted` → `confirmed` → `completed` / `cancelled`

`status/` endpointi ixtiyoriy `notes` ham qabul qiladi va uni **eski izohlar ustiga
vaqt shtampi bilan qo'shadi** (o'chirmaydi):

```json
{"status": "contacted", "notes": "Qo'ng'iroq qilindi, ertaga javob beradi"}
```
→ `notes` maydoniga `[06.08.2026 14:30] Qo'ng'iroq qilindi...` qo'shiladi.

> TODO'dagi ⚠️ *"og'ir texnika va to'y so'rovlarini faqat POST qilish mumkin"*
> muammosi shu bilan yopildi.

---

## 3. Javob formati

Loyihadagi mavjud `success_response` / `StandardPagination` bilan bir xil:

**Ro'yxat:**
```json
{
  "success": true,
  "data": {
    "count": 132,
    "total_pages": 7,
    "current_page": 1,
    "next": "http://localhost:8000/api/admin/orders/?page=2",
    "previous": null,
    "results": [ ... ]
  }
}
```

**Bitta obyekt / action:**
```json
{"success": true, "message": "Haydovchi tasdiqlandi", "data": { ... }}
```

**Xato:**
```json
{"success": false, "message": "Ma'lumotlar noto'g'ri", "errors": {"minimum_fare": ["..."]}}
```

Pagination: `?page=2&page_size=50` (maksimum 100).

---

## 4. Frontend uchun tez misollar

```bash
# Login qilib admin token olish
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"phone":"+998900000001","password":"parol"}'

TOKEN="<access_token>"

# Tasdiqlanmagan haydovchilar
curl "http://localhost:8000/api/admin/drivers/?is_active=false" \
  -H "Authorization: Bearer $TOKEN"

# Haydovchini tasdiqlash
curl -X PATCH "http://localhost:8000/api/admin/drivers/1/approve/" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"is_active": true}'

# Oxirgi 30 kun daromadi (grafik uchun)
curl "http://localhost:8000/api/admin/stats/revenue/?group_by=day" \
  -H "Authorization: Bearer $TOKEN"

# Bugungi bekor qilingan buyurtmalar
curl "http://localhost:8000/api/admin/orders/?status=cancelled&created_from=2026-08-06" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 5. Nima yopildi, nima qoldi

**Yopildi (TODO bo'yicha):**
- ✅ Admin API — 13 ta rejalashtirilgan endpoint + 9 ta qo'shimcha
- ✅ Og'ir texnika / to'y so'rovlarini ko'rish va status o'zgartirish
- ✅ `StandardPagination` — endi haqiqatan ishlatilyapti
- ✅ `django-filter` — endi haqiqatan ishlatilyapti
- ✅ `Order.cancel_reason` saqlanadi
- ✅ Buyurtmaga qo'lda haydovchi biriktirish (avtomatik biriktirish emas, lekin operator ishlay oladi)

**Shu API bilan bog'liq keyingi qadamlar:**
1. **CORS** — `prod.py` da `CORS_ALLOWED_ORIGINS` ro'yxatini to'ldiring, aks holda
   admin frontend ulana olmaydi (TODO 5-bo'lim).
2. **Throttling** — admin endpointlari ham hozircha cheksiz.
3. **Testlar** — `apps/common/tests/test_admin_api.py` yozish (permission + filtr + action).
4. **Audit log** — kim qaysi haydovchini bloklaganini yozib borish modeli.

---

## 6. Sinov natijasi

PostgreSQL 16 + PostGIS 3.4 da to'liq sinovdan o'tkazildi:

```
===== NATIJA: 45 ta OK, 0 ta XATO =====
```

Tekshirilgan holatlar: barcha 22 endpoint, filtr/qidiruv/ordering,
o'zini bloklashga urinish (400), superuser'ni bloklash (403),
yakunlangan buyurtmani bekor qilish (400), noto'g'ri status (400),
ishlatilayotgan tarifni o'chirish (soft delete), mijoz rolidan kirish (403),
tokensiz kirish (401).
