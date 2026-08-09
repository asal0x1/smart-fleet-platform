# SMART FLEET — API test checklist (ketma-ketlik bilan)

Base URL: `http://localhost:8000`
Swagger: `http://localhost:8000/api/docs/`

Barcha javob formati: `{"success": true, "message": "...", "data": {...}}`

---

## 0. Ishga tushirishdan oldin (BLOKER)

- [ ] **`config/settings/base.py` YO'Q!** `dev.py` ichida `from .base import *` bor, lekin `base.py` fayli mavjud emas → server umuman ishga tushmaydi. Avval shuni yarating.
- [ ] `apps/*/migrations/` papkalarida faqat `__init__.py` bor — migration fayllari yo'q. `python manage.py makemigrations` qiling.
- [ ] PostgreSQL + PostGIS: `CREATE EXTENSION postgis;`
- [ ] `cp .env.example .env` va to'ldiring
- [ ] `python manage.py migrate`
- [ ] `python manage.py seed_tariffs` → 4 ta tarif (Standard/Comfort/Business/Premium)
- [ ] `python manage.py createsuperuser` (admin token uchun)
- [ ] `python manage.py runserver`

---

## 1. AUTH — `/api/auth/`

### 1.1 Register (mijoz)
`POST /api/auth/register/` — token kerak emas

```json
{
  "phone": "+998901112233",
  "password": "parol123",
  "role": "client",
  "full_name": "Asal Abduqodirova"
}
```

Kutilgan: `201`, `data.user_id`, `data.token`
- [ ] Ishladi
- [ ] **Takror** shu bodyni yana yuboring → `400` "Bu telefon raqam allaqachon ro'yxatdan o'tgan"
- [ ] `password` ni 5 ta harf qiling → `400` (min_length=6)
- [ ] `role` ni `"admin"` qiling → `400` (faqat client/driver ruxsat)
- [ ] `role` ni umuman yubormang → default `client` bo'lishi kerak

### 1.2 Register (haydovchi)
`POST /api/auth/register/`

```json
{
  "phone": "+998901112244",
  "password": "parol123",
  "role": "driver",
  "full_name": "Aliyev Vali"
}
```

- [ ] `201` va `role: "driver"`
- [ ] ⚠️ **Tekshiring:** register paytida `Driver` obyekti yaratilmaydi (faqat `/api/drivers/profile/` chaqirilganda yaratiladi). Bu ataylabmi?

### 1.3 Login (mijoz)
`POST /api/auth/login/`

```json
{
  "phone": "+998901112233",
  "password": "parol123"
}
```

Kutilgan: `access_token`, `refresh_token`, `expires_in`, `user`
- [ ] Ishladi → **`access_token` ni saqlang = `CLIENT_TOKEN`**
- [ ] Noto'g'ri parol → `400` "Telefon yoki parol noto'g'ri"
- [ ] Ro'yxatdan o'tmagan telefon → `400`
- [ ] ⚠️ `expires_in: "7d"` qattiq yozilgan (hardcoded) — JWT'ning haqiqiy muddati bilan mos keladimi? `base.py` dagi `SIMPLE_JWT` bilan solishtiring.

### 1.4 Login (haydovchi)
```json
{
  "phone": "+998901112244",
  "password": "parol123"
}
```
- [ ] **`access_token` ni saqlang = `DRIVER_TOKEN`**

### 1.5 Login (admin)
Superuser telefoni va paroli bilan.
- [ ] **`access_token` ni saqlang = `ADMIN_TOKEN`**

### 1.6 Send OTP
`POST /api/auth/send-otp/`

```json
{
  "phone": "+998901112233"
}
```

- [ ] `200`, `data.message_id: "mock-0000"`, `data.expires_in: 120`
- [ ] **Kodni terminal konsolidan oling** (`[MOCK SMS] -> +998901112233: SMART FLEET tasdiqlash kodi: 123456`)
- [ ] 3-4 marta ketma-ket yuboring → ⚠️ **rate limit yo'q**, cheksiz SMS yuborsa bo'ladi. Bu xavfsizlik muammosi.

### 1.7 Verify OTP
`POST /api/auth/verify-otp/`

```json
{
  "phone": "+998901112233",
  "otp": "123456"
}
```

- [ ] To'g'ri kod → `200` "Telefon tasdiqlandi" + `data.token`
- [ ] **Shu kodni yana yuboring** → `400` (is_used=True bo'lgan)
- [ ] Noto'g'ri kod (`"000000"`) → `400`
- [ ] Yangi kod olib, 2 daqiqa kutib yuboring → `400` (muddati o'tgan)
- [ ] Ro'yxatdan o'tmagan telefon bilan → `200` lekin `data` bo'sh (token yo'q) — to'g'rimi?
- [ ] Keyin `GET /api/auth/profile/` da `is_verified: true` bo'lganini tekshiring

### 1.8 Token refresh
`POST /api/auth/refresh/`

```json
{
  "refresh": "<login'dan olingan refresh_token>"
}
```

- [ ] `200`, yangi `access` qaytadi
- [ ] ⚠️ Bu endpoint standart SimpleJWT javobini beradi (`{"access": ...}`), qolgan endpointlar esa `{"success": true, "data": ...}` formatida. **Format bir xil emas** — frontend uchun muammo bo'lishi mumkin.

### 1.9 Profile GET
`GET /api/auth/profile/`
Header: `Authorization: Bearer CLIENT_TOKEN`

- [ ] `200`, `id, phone, role, full_name, email, avatar_url, is_verified, created_at`
- [ ] Tokensiz → `401`
- [ ] Buzilgan token bilan → `401`

### 1.10 Profile PATCH
`PATCH /api/auth/profile/`
Header: `Authorization: Bearer CLIENT_TOKEN`

```json
{
  "full_name": "Asal A.",
  "email": "asal@example.com",
  "avatar_url": "https://example.com/avatar.png"
}
```

- [ ] `200` "Profil yangilandi"
- [ ] `{"role": "admin"}` yuboring → o'zgarmasligi kerak (read_only)
- [ ] `{"phone": "+998900000000"}` yuboring → o'zgarmasligi kerak (read_only)
- [ ] `{"email": "notanemail"}` → `400`

---

## 2. DRIVERS — `/api/drivers/`

Barchasi `DRIVER_TOKEN` bilan (nearby'dan tashqari).

### 2.1 Driver profile GET
`GET /api/drivers/profile/`
Header: `Authorization: Bearer DRIVER_TOKEN`

- [ ] `200` — Driver obyekti avtomatik yaratiladi, `is_active: false`, `is_online: false`, `rating: "5.0"`, `total_trips: 0`
- [ ] **`CLIENT_TOKEN` bilan chaqiring** → `403` "Faqat haydovchilar uchun."

### 2.2 Driver profile PATCH
`PATCH /api/drivers/profile/`

```json
{
  "car_model": "Chevrolet Cobalt",
  "car_color": "oq",
  "car_number": "01A123BC",
  "license_number": "AB1234567"
}
```

- [ ] `200` "Profil yangilandi"
- [ ] `{"rating": 9.9}` yuboring → o'zgarmasligi kerak (read_only)
- [ ] `{"is_active": true}` yuboring → o'zgarmasligi kerak (read_only — faqat admin tasdiqlaydi)

### 2.3 Lokatsiya yangilash
`POST /api/drivers/location/`

```json
{
  "lat": 41.311081,
  "lng": 69.240562,
  "accuracy": 10.5
}
```

- [ ] `200` "Joylashuv yangilandi"
- [ ] `accuracy` siz yuboring → ishlashi kerak (required=False)
- [ ] ⚠️ `accuracy` qabul qilinadi lekin **hech qayerga saqlanmaydi** — kerakmi?
- [ ] `{"lat": 200, "lng": 500}` → ⚠️ **validatsiya yo'q**, xato koordinata saqlanadi. `lat` -90..90, `lng` -180..180 bo'lishi kerak.
- [ ] `lat` siz yuboring → `400`

### 2.4 Online/offline
`POST /api/drivers/online/`

```json
{
  "is_online": true
}
```

- [ ] `200`, `data.is_online: true`
- [ ] `{"is_online": false}` → `false`
- [ ] `{}` bo'sh body → `400`

### 2.5 Yaqin haydovchilar
`GET /api/drivers/nearby/?lat=41.311081&lng=69.240562&radius=5000`
Header: `Authorization: Bearer CLIENT_TOKEN`

- [ ] ⚠️ **Ehtimol bo'sh `[]` qaytadi!** Chunki filter `is_active=True` talab qiladi, lekin yangi haydovchida `is_active=False`. **Admin paneldan haydovchini `is_active=True` qiling**, keyin qayta tekshiring.
- [ ] `is_active=True` va `is_online=True` dan keyin → haydovchi ro'yxatda chiqadi
- [ ] `distance_m` va `eta_min` to'g'ri hisoblanganini tekshiring
- [ ] `radius` siz → default 5000
- [ ] `lat` siz → `400` "lat va lng majburiy"
- [ ] `?lat=abc&lng=xyz` → `400`
- [ ] `?radius=notanumber` → ⚠️ **500 xatosi beradi** (`int()` try/except ichida emas). Buni tekshiring.
- [ ] Haydovchini offline qiling → ro'yxatdan yo'qolishi kerak

---

## 3. ORDERS — `/api/orders/`

### 3.1 Tariflar
`GET /api/orders/tariffs/`
Header: `Authorization: Bearer CLIENT_TOKEN`

- [ ] `200`, 4 ta tarif, `base_fare` bo'yicha tartiblangan
- [ ] Tokensiz → `401`
- [ ] **`id` larni yozib oling** (estimate va order uchun kerak)

### 3.2 Narxni oldindan hisoblash
`POST /api/orders/estimate/`
Header: `Authorization: Bearer CLIENT_TOKEN`

```json
{
  "from_lat": 41.311081,
  "from_lng": 69.240562,
  "to_lat": 41.326500,
  "to_lng": 69.228000,
  "tariff_id": 1
}
```

- [ ] `200`, `estimated_price`, `distance_km`, `duration_min`
- [ ] Qo'lda hisoblang: `base_fare + per_km*km + per_minute*min`, `minimum_fare` dan kam bo'lmasligi kerak
- [ ] `tariff_id: 999` → `404` "Tarif topilmadi"
- [ ] Turli tariflarda narx oshib borishini tekshiring (Standard < Comfort < Business < Premium)
- [ ] **Internetni o'chirib** yuboring → OSRM ishlamaydi, haversine fallback ishlashi kerak (500 bermasin)
- [ ] Bir xil nuqta (from = to) → `minimum_fare` qaytishi kerak

### 3.3 Buyurtma yaratish
`POST /api/orders/`
Header: `Authorization: Bearer CLIENT_TOKEN`

```json
{
  "from_address": "Amir Temur ko'chasi 1, Toshkent",
  "from_lat": 41.311081,
  "from_lng": 69.240562,
  "to_address": "Chilonzor 9-kvartal, Toshkent",
  "to_lat": 41.275000,
  "to_lng": 69.204000,
  "tariff_id": 1,
  "payment_method": "cash"
}
```

- [ ] `201` "Buyurtma yaratildi", `status: "pending"`
- [ ] **`id` ni saqlang = `ORDER_ID`**
- [ ] `estimated_price` estimate bilan bir xilmi?
- [ ] `payment_method: "click"` bilan ham sinang
- [ ] `payment_method: "karta"` → `400` (faqat cash/click/payme)
- [ ] `tariff_id: 999` → `400` "Tarif topilmadi"
- [ ] `from_address` siz → `400`
- [ ] ⚠️ **`DRIVER_TOKEN` bilan yuboring** → hozir `201` beradi! Haydovchi o'ziga buyurtma yarata oladi. `IsClient` permission qo'shilishi kerakmi? — tekshiring.

### 3.4 Buyurtmalar ro'yxati
`GET /api/orders/`
Header: `Authorization: Bearer CLIENT_TOKEN`

- [ ] Faqat o'z buyurtmalari chiqadi
- [ ] `DRIVER_TOKEN` bilan → faqat o'ziga biriktirilgan buyurtmalar
- [ ] `ADMIN_TOKEN` bilan → barchasi
- [ ] `?status=pending` → filtrlash ishlaydi
- [ ] `?status=all` → hammasi
- [ ] `?status=bekorqilingan` (xato qiymat) → bo'sh ro'yxat (500 bermasin)
- [ ] ⚠️ **Pagination yo'q** — 1000 ta buyurtma bo'lsa hammasi bir javobda keladi

### 3.5 Ochiq buyurtmalar (haydovchi)
`GET /api/orders/available/`
Header: `Authorization: Bearer DRIVER_TOKEN`

- [ ] `200`, faqat `pending` statusdagi buyurtmalar
- [ ] `CLIENT_TOKEN` bilan → `403`
- [ ] ⚠️ Haydovchining joylashuviga qarab **filtrlanmaydi** — Toshkentdagi haydovchi Samarqand buyurtmasini ham ko'radi

### 3.6 Buyurtma detali
`GET /api/orders/{ORDER_ID}/`

- [ ] Egasi (`CLIENT_TOKEN`) → `200`
- [ ] `ADMIN_TOKEN` → `200`
- [ ] **Boshqa mijoz tokeni bilan** → `403` "Ruxsat yo'q" ✅ muhim test
- [ ] Mavjud bo'lmagan id (`/api/orders/99999/`) → `404`

---

## 4. STATUS FLOW — `PATCH /api/orders/{id}/status/`

Ruxsat etilgan yo'l:
`pending → accepted → driver_arrived → ongoing → completed`
Har bir bosqichdan `cancelled` ga o'tish mumkin.

### 4.1 Qabul qilish
`PATCH /api/orders/{ORDER_ID}/status/`
Header: `Authorization: Bearer DRIVER_TOKEN`

```json
{ "status": "accepted" }
```

- [ ] `200`, `status: "accepted"`, `accepted_at` to'ldi, `driver` obyekti keldi

### 4.2 Haydovchi yetib keldi
```json
{ "status": "driver_arrived" }
```
- [ ] `200`

### 4.3 Yo'lda
```json
{ "status": "ongoing" }
```
- [ ] `200`, `started_at` to'ldi

### 4.4 Yakunlash
```json
{ "status": "completed" }
```
- [ ] `200`, `completed_at` to'ldi, `final_price = estimated_price`
- [ ] `GET /api/drivers/profile/` → `total_trips` 1 ga oshdi

### 4.5 Noto'g'ri o'tishlar (MUHIM)
- [ ] Yakunlangan buyurtmaga yana `{"status": "ongoing"}` → `400` "o'tish mumkin emas"
- [ ] Yangi `pending` buyurtmaga to'g'ridan-to'g'ri `{"status": "completed"}` → `400`
- [ ] `pending` → `{"status": "driver_arrived"}` → `400`
- [ ] `{"status": "pending"}` → `400` (choices ichida yo'q)
- [ ] `{"status": "xyz"}` → `400`

### 4.6 Bekor qilish
Yangi buyurtma yarating, keyin:
```json
{ "status": "cancelled" }
```
- [ ] `pending` dan → `200`
- [ ] `accepted` dan → `200`
- [ ] `cancelled` dan yana `cancelled` → `400`

### 4.7 ⚠️ XAVFSIZLIK — bu testni albatta qiling
- [ ] **Boshqa mijoz tokeni** bilan begona buyurtma statusini o'zgartiring → hozir **ishlab ketadi!** Egalik tekshiruvi yo'q (`ChangeStatusView` da faqat `IsAuthenticated`).
- [ ] **`CLIENT_TOKEN` bilan `{"status": "accepted"}`** yuboring → mijoz uchun ham `Driver` obyekti yaratiladi (`get_or_create_driver`) va u haydovchi bo'lib qoladi. Jiddiy bug.
- [ ] Bir buyurtmani ikki xil haydovchi navbat bilan `accepted` qilishga urinsin

---

## 5. PAYMENTS — `/api/payments/`

### 5.1 To'lov boshlash
`POST /api/payments/create/`
Header: `Authorization: Bearer CLIENT_TOKEN`

```json
{
  "order_id": 1,
  "method": "click"
}
```

- [ ] `200`, `payment_id`, `click_url`, `status: "pending"`
- [ ] `click_url` ichida `service_id`, `merchant_id`, `amount`, `transaction_param` bormi
- [ ] `{"order_id": 1, "method": "cash"}` → `click_url` siz javob
- [ ] Begona buyurtma id bilan → `404` "Buyurtma topilmadi"
- [ ] `order_id` siz → `404`
- [ ] ⚠️ Bitta buyurtma uchun 3 marta chaqiring → har safar **yangi Payment yaratiladi**, dublikat tekshiruvi yo'q
- [ ] ⚠️ Allaqachon to'langan buyurtma uchun chaqiring → baribir ruxsat beradi
- [ ] ⚠️ `estimated_price` va `final_price` ikkalasi ham `null` bo'lgan buyurtma bilan → `amount=None` → **500 xatosi** bo'lishi kerak

### 5.2 Click Prepare (webhook)
`POST /api/payments/click/prepare/` — token kerak emas
Content-Type: `application/x-www-form-urlencoded` (Click shunday yuboradi)

```json
{
  "click_trans_id": "123456789",
  "service_id": "12345",
  "click_paydoc_id": "987654",
  "merchant_trans_id": "1",
  "amount": "25000.00",
  "action": "0",
  "error": "0",
  "error_note": "Success",
  "sign_time": "2026-08-05 12:00:00",
  "sign_string": "<MD5 hash>"
}
```

`sign_string` ni shunday hisoblang:
```
md5(click_trans_id + service_id + SECRET_KEY + merchant_trans_id + amount + action + sign_time)
```

Python bilan:
```python
import hashlib
raw = "123456789" + "12345" + "SECRET_KEY" + "1" + "25000.00" + "0" + "2026-08-05 12:00:00"
print(hashlib.md5(raw.encode()).hexdigest())
```

- [ ] To'g'ri imzo → `{"error": 0, "merchant_prepare_id": ...}`
- [ ] Noto'g'ri `sign_string` → `{"error": -1}` ✅ muhim
- [ ] `merchant_trans_id: "99999"` (yo'q buyurtma) → `{"error": -5}`
- [ ] ⚠️ **`amount` tekshirilmaydi!** Buyurtma narxi 25000 bo'lsa ham, `amount: "1.00"` yuborilsa qabul qilinadi. `-2` (INVALID_AMOUNT) qaytishi kerak edi.
- [ ] ⚠️ Barcha javoblar HTTP `200` — Click uchun to'g'rimi, tekshiring

### 5.3 Click Complete (webhook)
`POST /api/payments/click/complete/`

```json
{
  "click_trans_id": "123456789",
  "service_id": "12345",
  "merchant_trans_id": "1",
  "merchant_prepare_id": "1",
  "amount": "25000.00",
  "action": "1",
  "error": "0",
  "error_note": "Success",
  "sign_time": "2026-08-05 12:01:00",
  "sign_string": "<MD5 hash>"
}
```

Imzo (prepare'dan farqli — `merchant_prepare_id` qo'shiladi):
```
md5(click_trans_id + service_id + SECRET_KEY + merchant_trans_id + merchant_prepare_id + amount + action + sign_time)
```

- [ ] To'g'ri imzo → `{"error": 0}`, Payment `paid`, Order `payment_status: "paid"`
- [ ] Noto'g'ri imzo → `{"error": -1}`
- [ ] **Shu so'rovni yana yuboring** → `{"error": -4}` (allaqachon to'langan)
- [ ] `"error": "-9"` bilan yuboring → Payment `cancelled` bo'ladi
- [ ] ⚠️ `error: -9` holatida **barcha** Payment'lar bekor qilinadi (`filter(order=order).update(...)`) — bitta buyurtmada bir nechta to'lov bo'lsa muammo
- [ ] ⚠️ Prepare qilinmagan buyurtma uchun to'g'ridan-to'g'ri complete yuboring → o'tib ketadi. `merchant_prepare_id` tekshirilmaydi.
- [ ] ⚠️ Payment yozuvi yo'q bo'lsa ham `order.payment_status = "paid"` bo'ladi
- [ ] ⚠️ Bu yerda ham `amount` tekshirilmaydi

---

## 6. SO'ROVLAR (token kerak emas)

### 6.1 Og'ir texnika
`POST /api/heavy-equipment/requests/`

```json
{
  "category": "earth",
  "items": [
    { "name": "Ekskavator", "quantity": 2 },
    { "name": "Buldozer", "quantity": 1 }
  ],
  "address": "Yunusobod tumani, Toshkent",
  "lat": 41.360000,
  "lng": 69.290000,
  "start_date": "2026-08-20",
  "start_time": "09:00:00",
  "duration_days": 3,
  "contact_name": "Asal Abduqodirova",
  "contact_phone": "+998901112233",
  "notes": "Yer ishlari uchun kerak"
}
```

- [ ] `201`, `request_id`, `status: "pending"`
- [ ] **Terminal konsolida email chiqqanini tekshiring** (console backend)
- [ ] `category: "lift"` / `"road"` / `"loader"` bilan ham sinang
- [ ] `category: "boshqa"` → `400`
- [ ] `items: []` bo'sh massiv → o'tadimi? (min_length yo'q) — tekshiring
- [ ] `items: [{"name": "Kran", "quantity": 0}]` → `400` (min_value=1)
- [ ] `items: "matn"` → `400`
- [ ] `start_date: "2020-01-01"` (o'tgan sana) → ⚠️ **qabul qilinadi**, validatsiya yo'q
- [ ] `start_date: "20-08-2026"` (noto'g'ri format) → `400`
- [ ] `lat`, `lng`, `start_time`, `notes` siz yuboring → ishlashi kerak
- [ ] `address` siz → `400`
- [ ] `contact_phone: "salom"` → ⚠️ qabul qilinadi, telefon formati tekshirilmaydi
- [ ] ⚠️ Token kerak emas + rate limit yo'q → **spam qilish mumkin**. 20 ta so'rov yuborib ko'ring.

### 6.2 To'y transporti
`POST /api/wedding/requests/`

```json
{
  "car_brand": "Mercedes-Benz S-Class",
  "car_count": 3,
  "decoration_type": "flowers",
  "address": "Mirzo Ulug'bek tumani, Toshkent",
  "date": "2026-09-15",
  "time": "14:00:00",
  "duration_hours": 4,
  "contact_name": "Asal Abduqodirova",
  "contact_phone": "+998901112233",
  "notes": "Oq mashinalar bo'lsin"
}
```

- [ ] `201`, `estimated_price` = `car_count × duration_hours × 125000` = **1 500 000** ✅ qo'lda hisoblab tekshiring
- [ ] Konsolda email chiqdimi
- [ ] `decoration_type: "balloons"` / `"ribbons"` bilan sinang
- [ ] `decoration_type: "gullar"` → `400`
- [ ] `decoration_type` siz → o'tishi kerak (blank=True)
- [ ] `car_count: 0` → ⚠️ `estimated_price: 0` bo'ladi. `min_value=1` kerakmi?
- [ ] `car_count: 1000000` → ⚠️ juda katta narx, yuqori chegara yo'q
- [ ] `car_count: -1` → `400` (PositiveIntegerField)
- [ ] `estimated_price` ni body'da yuboring → e'tiborga olinmasligi kerak (read_only)
- [ ] `date` siz → `400`
- [ ] ⚠️ 125000 narxi kodda qattiq yozilgan (`views.py`) — DB'ga ko'chirish kerakmi?

---

## 7. ADMIN — `/api/admin/stats/`

`GET /api/admin/stats/`
Header: `Authorization: Bearer ADMIN_TOKEN`

- [ ] `200`, maydonlar: `total_users`, `total_drivers`, `active_drivers`, `online_drivers`, `total_orders`, `completed_orders`, `pending_orders`, `cancelled_orders`, `total_revenue`, `orders_by_status`
- [ ] Raqamlar haqiqatga mos keladimi (DB bilan solishtiring)
- [ ] `total_revenue` = yakunlangan buyurtmalar `final_price` yig'indisi
- [ ] **`CLIENT_TOKEN` bilan** → `403` "Faqat administratorlar uchun."
- [ ] **`DRIVER_TOKEN` bilan** → `403`
- [ ] Tokensiz → `401`
- [ ] ⚠️ `total_users` faqat `role="client"` ni sanaydi — nomi chalg'ituvchi

---

## 8. Umumiy tekshiruvlar

- [ ] `GET /api/docs/` — Swagger ochiladimi, barcha endpointlar ko'rinadimi
- [ ] `GET /api/schema/` — schema yuklanadimi
- [ ] `/admin/` — Django admin ishlaydimi, barcha modellar ro'yxatda bormi
- [ ] Muddati o'tgan token bilan har bir himoyalangan endpoint → `401`
- [ ] `Authorization: Bearer xyz` (buzilgan) → `401`
- [ ] Har bir POST'ga bo'sh `{}` body yuboring → `400` bo'lsin, `500` emas
- [ ] Har bir POST'ga noto'g'ri JSON yuboring → `400`
- [ ] Xato javoblari `{"success": false, "message": ...}` formatidami? (`apps/common/exceptions.py` handler ulanganini tekshiring)
- [ ] CORS: frontend domenidan so'rov o'tadimi

---

## 9. Topilgan asosiy muammolar (ustuvorlik bo'yicha)

| # | Muammo | Joyi | Jiddiylik |
|---|--------|------|-----------|
| 1 | `config/settings/base.py` fayli yo'q — loyiha ishga tushmaydi | `config/settings/` | 🔴 Bloker |
| 2 | Migration fayllari yo'q | `apps/*/migrations/` | 🔴 Bloker |
| 3 | Status o'zgartirishda egalik tekshiruvi yo'q — istalgan user begona buyurtmani boshqaradi | `orders/views.py:ChangeStatusView` | 🔴 Xavfsizlik |
| 4 | Mijoz `accepted` yuborsa o'ziga Driver obyekti yaratiladi | `orders/views.py:122` | 🔴 Xavfsizlik |
| 5 | Click webhook'da `amount` tekshirilmaydi | `payments/views.py` | 🔴 Moliyaviy |
| 6 | Complete'da `merchant_prepare_id` tekshirilmaydi | `payments/views.py` | 🟠 Moliyaviy |
| 7 | OTP yuborishda rate limit yo'q | `users/views.py:SendOTPView` | 🟠 Xavfsizlik |
| 8 | So'rov endpointlarida (heavy/wedding) auth ham, rate limit ham yo'q | `requests/views.py` | 🟠 Spam |
| 9 | Yangi haydovchi `is_active=False` → `nearby/` bo'sh qaytadi | `drivers/models.py` | 🟠 Mantiq |
| 10 | Haydovchi ham buyurtma yarata oladi (`IsClient` yo'q) | `orders/views.py` | 🟡 Mantiq |
| 11 | `radius` noto'g'ri bo'lsa 500 xatosi | `drivers/views.py:77` | 🟡 |
| 12 | lat/lng chegaralari tekshirilmaydi | `drivers/serializers.py` | 🟡 |
| 13 | Buyurtmalar ro'yxatida pagination yo'q | `orders/views.py` | 🟡 |
| 14 | `refresh/` javob formati boshqalardan farq qiladi | `users/urls.py` | 🟡 |
| 15 | `expires_in: "7d"` hardcoded | `users/views.py:52` | 🟡 |
| 16 | `available/` haydovchi joylashuvi bo'yicha filtrlamaydi | `orders/views.py` | 🟡 |
| 17 | To'y narxi (125000) kodda hardcoded | `requests/views.py:14` | 🟢 |
| 18 | `accuracy` qabul qilinadi lekin saqlanmaydi | `drivers/serializers.py` | 🟢 |
