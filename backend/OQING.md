# SMART FLEET — Backend MVP tayyor

```
410 test o'tdi · qamrov 93% · ruff toza · makemigrations --check toza
```

Bu arxivda **faqat o'zgargan va yangi fayllar** bor. Repongiz ustiga
nusxalash yetarli.

---

## O'rnatish

```bash
cp -r smartfleet-update/. /sizning/loyihangiz/

pip install -r requirements/base.txt
pip install -r requirements/dev.txt

python manage.py migrate
python manage.py check
pytest
```

### ⚠️ Ishga tushirish endi boshqacha

WebSocket qo'shilgani uchun **gunicorn ishlamaydi** — u WSGI, WebSocket'ni
qo'llab-quvvatlamaydi. `/ws/` yo'llari umuman javob bermaydi.

```bash
# Dev
python manage.py runserver          # daphne avtomatik ishlaydi

# Prod
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

`Dockerfile` va `docker-compose.yml` allaqachon yangilangan.

### ⚠️ Redis endi majburiy

Prod'da Redis'siz ikki narsa buziladi:
1. WebSocket xabarlari faqat bitta worker ichida qoladi — mijoz boshqa
   worker'ga ulangan bo'lsa hech nima olmaydi
2. Throttle hisoblagichlari har worker'da alohida

`docker-compose.yml` ga Redis servisi qo'shildi. `prod.py` `REDIS_URL`
bo'lmasa ogohlantiradi.

---

## Nima qo'shildi

### 1. Real-time (WebSocket)

Yangi app: `apps/notifications/`

```
ws://host/ws/notifications/?token=<access>   — shaxsiy kanal
ws://host/ws/orders/<id>/?token=<access>     — bitta buyurtmani kuzatish
```

Token **query string'da** — brauzerning WebSocket API'si maxsus header
yubora olmaydi, shuning uchun `Authorization` ishlatib bo'lmaydi.

**Nima yuboriladi:**

| Voqea | Kimga | Xabar turi |
|---|---|---|
| Yangi buyurtma | Barcha tasdiqlangan onlayn haydovchilar | `new_order` |
| Status o'zgardi | Mijoz + haydovchi + admin | `order_event` |
| Haydovchi joylashuvi | Faol safarning mijozi | `driver_location` |
| Shaxsiy xabar | Foydalanuvchi | `notification` |

Klient `{"action": "ping"}` va `{"action": "mark_read", "id": N}` yubora oladi.

**Ruxsatlar:** tokensiz ulanish `4401` bilan yopiladi, begona odam
buyurtma kanaliga ulansa `4403`.

**Muhim qaror:** WebSocket xatosi asosiy oqimni **buzmaydi**. Channel
layer yiqilsa `notify_*` funksiyalari faqat log qoldiradi — buyurtma
baribir yaratiladi va status o'zgaradi. Real-time qulaylik, bog'liqlik emas.

### 2. Bildirishnomalar (REST)

Ilova yopiq bo'lganda ham xabarlar yo'qolmasligi uchun bazaga yoziladi:

```
GET   /api/notifications/?is_read=false
PATCH /api/notifications/{id}/read/
PATCH /api/notifications/read-all/
```

Ro'yxat javobida `unread` soni ham bor — badge uchun.

### 3. Geocode proxy

```
GET /api/geocode/?q=Chilonzor 5-kvartal
GET /api/geocode/reverse/?lat=41.31&lng=69.24
```

`services/map.py` dagi o'lik kod endi ishlatilyapti.

**Nega proxy:** Yandex kalitini brauzerga chiqarib bo'lmaydi — o'g'irlab,
sizning hisobingizdan so'rov yog'diradilar. Endpoint token talab qiladi,
60/min cheklangan va natijalar 24 soat keshlanadi (Yandex so'rovlari
limitli).

### 4. Yakuniy narx haqiqiy masofa bo'yicha

Ilgari `final_price` har doim `estimated_price` ga teng edi — haydovchi
boshqa yo'ldan yursa ham narx o'zgarmasdi.

```json
PATCH /api/orders/{id}/status/
{"status": "completed", "actual_distance_km": 12.5}
```

Haqiqiy safar vaqti (`started_at` → `completed_at`) ham hisobga olinadi.
**Xavfsizlik chegarasi:** yakuniy narx kelishilgan narxdan 3 barobardan
oshmaydi — GPS xatosi mijozga zarar qilmasligi uchun.

`actual_distance_km` berilmasa eski xatti-harakat saqlanadi.

### 5. Naqd to'lovni tasdiqlash

```
PATCH /api/payments/{id}/confirm-cash/
```

Ilgari naqd to'lov hech qachon `paid` bo'lmasdi — buyurtma yakunlansa ham
to'lov holati abadiy `pending` bo'lib qolardi.

Faqat biriktirilgan haydovchi yoki admin, faqat yakunlangan safar uchun.
Mijozga xabar boradi.

### 6. Og'ir texnika narxi

Ilgari umuman hisoblanmasdi. Endi `estimated_price` maydoni va formula:

```
sum(dona) × kunlik_narx(kategoriya) × kunlar
```

Narxlar `.env` da: `HEAVY_RATE_EARTH`, `HEAVY_RATE_LIFTING`, va h.k.

---

## Frontend uchun qisqacha

**Mijoz ilovasi oqimi:**
1. `POST /api/auth/login/` → token
2. `ws://.../ws/notifications/?token=...` ga ulanish
3. Manzil kiritish → `GET /api/geocode/?q=...`
4. `POST /api/orders/estimate/` → narx ko'rsatish
5. `POST /api/orders/` → buyurtma
6. `ws://.../ws/orders/<id>/?token=...` ga ulanish
7. `order_event` va `driver_location` xabarlarini tinglash
8. Yakunlangach `POST /api/orders/<id>/review/`

**Haydovchi ilovasi oqimi:**
1. Login → `POST /api/drivers/documents/` (hujjatlar)
2. Admin tasdig'ini kutish (`documents_complete`, `is_active`)
3. `POST /api/drivers/online/` → onlayn
4. WebSocket'dan `new_order` kutish
5. `PATCH /api/orders/<id>/status/` `accepted` → birinchi bosgan oladi (409 = kech qoldingiz)
6. Har 5–10 soniyada `POST /api/drivers/location/`
7. Yakunda `completed` + `actual_distance_km`
8. Naqd bo'lsa `PATCH /api/payments/<id>/confirm-cash/`

Swagger: `/api/docs/`

---

## Backend MVP bo'yicha yopilgan

| Ish | Holat |
|---|---|
| Admin API (22 endpoint) | ✅ |
| Xavfsizlik (15 punkt) | ✅ |
| Testlar + CI | ✅ 410 ta |
| Django admin | ✅ |
| Fayl yuklash + hujjat tasdiqlash | ✅ |
| Reyting va sharhlar | ✅ |
| **Real-time (WebSocket)** | ✅ |
| **Geocode proxy** | ✅ |
| **Yakuniy narx** | ✅ |
| **Naqd to'lov** | ✅ |
| **Og'ir texnika narxi** | ✅ |
| CORS, Redis, daphne, docker | ✅ |

---

## MVP'ga kirmagan (ataylab)

Bularni **birinchi mijozlardan keyin**, real ehtiyojga qarab qilish kerak.
Hozir qilinsa, ishlatilmaydigan kod bo'lib qolishi mumkin:

| Ish | Nega keyinroq |
|---|---|
| Payme | Click ishlayapti, ikkinchisi shart emas |
| Promo-kod, refund, kutish to'lovi, jarima | Biznes qarorlar kerak |
| Haydovchi balansi va komissiya | Komissiya foizi hali aniqlanmagan |
| Ko'p tillilik (i18n) | Avval o'zbek bozorida sinash |
| Avtomatik haydovchi biriktirish | Hozir e'lon hammaga ketadi, birinchi qabul qilgan oladi — MVP uchun yetarli va soddaroq |
| Audit log | Foydali, lekin bloker emas |
| Celery | SMS sinxron yuboriladi (~1 soniya). Yuk oshganda kerak bo'ladi |

## Deploy uchun qolgan

Bu ikkitasi kodda emas, infratuzilmada:

1. **Nginx + SSL** — reverse proxy, Let's Encrypt, `/ws/` uchun
   `proxy_set_header Upgrade` sozlamasi (WebSocket'siz proxy ulanishni uzadi)
2. **Sentry + logging + backup cron**

`prod.py` da `SECURE_SSL_REDIRECT` va `SECURE_HSTS_SECONDS` tayyor,
sertifikat o'rnatgach `.env` da yoqasiz.

---

## Test qilish

```bash
pytest                              # 410 ta
pytest tests/test_mvp.py            # yangi funksiyalar (44 ta)
pytest -k WebSocket                 # WebSocket (8 ta)
pytest --cov=apps --cov=services --cov-report=term-missing
ruff check apps config services tests
```

WebSocket testlari `InMemoryChannelLayer` bilan ishlaydi — Redis kerak emas.
