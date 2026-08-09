# SMART FLEET — 1-navbat xavfsizlik tuzatishlari

TODO'ning 1-navbatidagi **15 ta punkt** yopildi.
PostgreSQL 16 + PostGIS 3.4 da sinovdan o'tkazildi: **52/52 test OK**,
Admin API regressiyasi ham tekshirildi: **45/45 OK**.

---

## O'rnatish

### 1. Yangi fayllar

```
apps/common/validators.py     ← yangi
apps/common/throttling.py     ← yangi
```

### 2. Almashtiriladigan fayllar

```
apps/users/serializers.py
apps/users/views.py
apps/users/urls.py
apps/users/admin.py
apps/orders/views.py
apps/orders/serializers.py
apps/drivers/views.py
apps/drivers/serializers.py
apps/requests/views.py
apps/requests/serializers.py
apps/payments/views.py
services/payment.py
config/settings/base.py        ← CORS tuzatishi ham shu faylda
.env.example
```

### 3. Migratsiya

`token_blacklist` app'i qo'shilgani uchun:

```bash
python manage.py migrate
```

Model o'zgarishi yo'q — faqat SimpleJWT'ning o'z jadvallari yaratiladi.

### 4. Tekshirish

```bash
python manage.py check
python manage.py runserver
```

---

## Nima tuzatildi

### 1.1 Buyurtma egaligi ⚠️ eng katta teshik

**Ilgari:** `ChangeStatusView` da hech qanday tekshiruv yo'q edi — istalgan
foydalanuvchi istalgan buyurtma statusini o'zgartira olardi.

**Endi** — rolga qarab aniq qoidalar:

| Status | Kim qila oladi |
|---|---|
| `accepted` | Faqat **tasdiqlangan** haydovchi, buyurtma bo'sh bo'lsa |
| `driver_arrived`, `ongoing`, `completed` | Faqat shu buyurtmaga **biriktirilgan** haydovchi |
| `cancelled` | Buyurtma egasi, biriktirilgan haydovchi yoki admin |

Qo'shimcha:
- `get_or_create_driver()` endi `role != "driver"` bo'lsa `None` qaytaradi.
  **Mijoz `accepted` yuborsa unga Driver obyekti yaratilmaydi.**
- Buyurtma qabul qilishda `select_for_update(of=("self",))` — ikki haydovchi
  bir vaqtda bosса, ikkinchisi `409` oladi (poyga holati yopildi).
- Haydovchi buyurtma bera olmaydi (`POST /api/orders/` → 403).
- Tasdiqlanmagan haydovchi `available/` da hech nima ko'rmaydi va
  onlayn bo'la olmaydi.

> **Eslatma:** `of=("self",)` shart. `driver` maydoni nullable bo'lgani uchun
> `select_related` LEFT OUTER JOIN yasaydi, PostgreSQL esa uni qulflashga
> ruxsat bermaydi. Bu xato testda topildi.

### 1.2 Click to'lovi

**Ilgari:** imzo tekshirilardi, lekin **summa tekshirilmasdi**. Imzo faqat
so'rov o'zgartirilmaganini isbotlaydi, summaning to'g'riligini emas —
hujumchi 1000 so'mlik to'lov yaratib 500 000 so'mlik buyurtmani yopa olardi.

**Endi:**
- `check_amount()` — prepare **va** complete bosqichida (`error: -2`)
- `merchant_prepare_id` = bizning `Payment.id`, complete'da tekshiriladi (`-6`)
- Idempotentlik — takroriy webhook `-4` oladi, `select_for_update` bilan
- Bekor qilingan buyurtmaga to'lov o'tmaydi (`-9`)
- IP whitelist: `CLICK_ALLOWED_IPS` (CIDR ham qo'llab-quvvatlanadi).
  Bo'sh bo'lsa tekshiruv o'chiq — dev uchun. **Prod'da to'ldiring.**
- `CreatePaymentView`: allaqachon to'langan/bekor qilingan buyurtmani rad etadi
  va har bosishda yangi `Payment` yaratmaydi

### 1.3 Throttling

Ilgari kodda birorta `throttle` yo'q edi.

| Endpoint | Cheklov | Kalit |
|---|---|---|
| `send-otp/` | 3/soat | **telefon raqam** |
| `verify-otp/` | 10/soat | telefon raqam |
| `login/` | 10/soat | IP |
| `register/` | 10/soat | IP |
| `heavy-equipment/`, `wedding/` | 5/soat | IP |
| `reset-password/` | 5/soat | telefon raqam |
| Qolgan hamma | 60/min anon, 300/min user | IP / user |

Hammasi `.env` orqali sozlanadi (`THROTTLE_OTP=3/hour` va h.k.).

OTP nega IP emas, **telefon** bo'yicha: bitta hujumchi ko'p IP'dan bitta
raqamga SMS yog'dira oladi; aksincha, bitta uy Wi-Fi'sidan bir nechta odam
ro'yxatdan o'tishi normal holat.

> ⚠️ **Prod'da Redis kerak.** Throttle hisoblagichlari cache'da saqlanadi.
> Standart `LocMemCache` har bir gunicorn worker uchun alohida — 3 worker
> bo'lsa cheklov amalda 3 barobar yumshoq. `.env` ga `REDIS_URL=redis://redis:6379/1`
> yozsangiz avtomatik Redis'ga o'tadi (kod tayyor).

### 1.4 Auth

Yangi endpointlar:

| Method | URL | Tavsif |
|---|---|---|
| POST | `/api/auth/logout/` | `{"refresh_token": "..."}` → blacklist |
| POST | `/api/auth/change-password/` | `{"old_password", "new_password"}` |
| POST | `/api/auth/reset-password/` | `{"phone", "otp", "new_password"}` |

- `token_blacklist` app'i ulandi, `BLACKLIST_AFTER_ROTATION = True` —
  refresh token rotatsiyadan keyin eskisi ishlamaydi
- Parolga Django validatorlari qo'llanadi (zaif parol rad etiladi)
- Parol tiklashda "bunday user yo'q" xabari **berilmaydi** — aks holda
  qaysi raqamlar ro'yxatdan o'tganini aniqlab olish mumkin bo'lardi

**Token muddati o'zgardi:** access `7 kun` → `60 daqiqa`, refresh 30 kun.
7 kunlik access token'da logout deyarli ma'nosiz: o'g'irlangan token
bir hafta ishlayveradi. `.env` da `ACCESS_TOKEN_MINUTES` bilan sozlanadi.

> 🔴 **Frontend'ga ta'sir qiladi:** `login/` javobidagi `expires_in` endi
> `"7d"` (matn) emas, **soniyalarda son** (`3600`). Frontend token
> yangilashni `refresh/` orqali qilishi kerak.

### 1.5 Validatsiya

`apps/common/validators.py`:

- `PhoneField` — `+998XXXXXXXXX` regex + **avtomatik normalizatsiya**.
  Qabul qiladi: `+998 90 123-45-67`, `998901234567`, `901234567` →
  hammasi `+998901234567` bo'lib saqlanadi
- `LatitudeField` (-90..90), `LongitudeField` (-180..180)
- `nearby/` uchun `radius` 100–50 000 m, `limit` 1–50 oralig'ida.
  Ilgari `?radius=99999999` butun bazani PostGIS orqali skanerlab
  serverni qotirib qo'yishi mumkin edi

Qo'llanilgan joylar: register, login, OTP, parol tiklash, buyurtma yaratish,
narx hisoblash, haydovchi lokatsiyasi, `nearby/`, og'ir texnika va to'y so'rovlari.

### 1.6 Django admin

`UserAdmin` → `BaseUserAdmin`:
- parol xesh ochiq matn sifatida ko'rinmaydi
- admin'dan user yaratganda parol **to'g'ri hash qilinadi**
  (`add_fieldsets` bilan `password1`/`password2`)
- `date_hierarchy`, kengaytirilgan `list_filter`, yig'iladigan "Ruxsatlar" bo'limi

---

## Sinov natijasi

```
===== 1.5 TELEFON VA KOORDINATA VALIDATSIYASI =====   9/9
===== 1.1 BUYURTMA EGALIGI =====                      14/14
===== 1.3 THROTTLING =====                             4/4
===== 1.4 LOGOUT / PAROL =====                        13/13
===== 1.2 CLICK TO'LOVI =====                         11/11
===== 1.6 DJANGO ADMIN =====                           1/1
===== NATIJA: 52 ta OK, 0 ta XATO =====

Admin API regressiyasi: 45 ta OK, 0 ta XATO
```

Alohida tekshirilgan hujum ssenariylari:
- begona mijoz buyurtma statusini o'zgartirishi → 403
- mijoz `accepted` yuborib haydovchiga aylanishi → 403, Driver yaratilmadi
- tasdiqlanmagan haydovchi buyurtma olishi → 403
- ikki haydovchi bir buyurtmani olishi → 409
- 1000 so'mga 500 000 so'mlik buyurtmani "to'lash" → `-2`
- prepare'siz to'g'ridan-to'g'ri complete → `-6`
- takroriy Click webhook → `-4`
- soxta imzo → `-1`
- bitta raqamga 4-marta OTP → `429`

---

## Prod'ga chiqishdan oldin `.env` da to'ldiring

```bash
SECRET_KEY=<uzun tasodifiy satr>
ALLOWED_HOSTS=smartfleet.uz,api.smartfleet.uz
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://admin.smartfleet.uz,https://smartfleet.uz

REDIS_URL=redis://redis:6379/1          # throttling to'g'ri ishlashi uchun
CLICK_ALLOWED_IPS=<Click bergan IP/CIDR>
CLICK_SECRET_KEY=<...>
ESKIZ_MOCK=False
ESKIZ_EMAIL=<...>
ESKIZ_PASSWORD=<...>
```

---

## Yo'l-yo'lakay topilgan, lekin tuzatilmagan

1. **Javob formati bir xil emas.** `GET /api/orders/available/` va
   `GET /api/orders/tariffs/` — `ListAPIView` bo'lgani uchun `{"success": ...}`
   konvertisiz, to'g'ridan-to'g'ri massiv qaytaradi. Boshqa hamma joyda
   konvert bor. Frontend uchun chalkash — bir xilga keltirish kerak.
2. **Eskiz token bug'i** (6-navbat) hali turibdi: token `self._token` da
   xotirada, ko'p worker'da har biri alohida login qiladi.
3. **`change_status` da `final_price = estimated_price`** — haqiqiy masofa
   bo'yicha qayta hisoblanmaydi (3-navbat).

Keyingi mantiqiy qadam — **2-navbat: testlar**. Yuqoridagi 52 ta tekshiruvni
`pytest` fayllariga ko'chirish yaxshi boshlanish bo'ladi, chunki senariylar
allaqachon yozilgan.
