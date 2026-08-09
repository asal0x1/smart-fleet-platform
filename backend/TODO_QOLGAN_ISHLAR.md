# SMART FLEET — Qolgan ishlar

## Admin panel — bormi?

**Qisman bor.** Ikki xil "admin panel" tushunchasini ajratish kerak:

| Nima | Holat | Izoh |
|------|-------|------|
| **Django admin** (`/admin/`) | ✅ **Bor va yaxshi sozlangan** | 6 ta model ro'yxatda: User, OTPCode, Driver, Tariff, Order, Payment, HeavyEquipmentRequest, WeddingRequest. `list_display`, `list_filter`, `search_fields` bor. Driver va Order uchun `GISModelAdmin` (xaritada nuqta ko'rinadi). |
| **Admin API** (frontend uchun) | ❌ **Deyarli yo'q** | Faqat bitta endpoint: `GET /api/admin/stats/`. Boshqa hech narsa yo'q. |
| **Admin frontend** (React/Vue panel) | ❌ **Yo'q** | Loyihada faqat backend bor. |

### Django admin'da yetishmayotgan narsalar

- [ ] `UserAdmin` oddiy `ModelAdmin` — **parol maydoni ochiq matn** ko'rinadi. `BaseUserAdmin` ga o'tkazish yoki `fieldsets` sozlash kerak
- [ ] Admin'dan user yaratib bo'lmaydi (parol hash qilinmaydi)
- [ ] Haydovchini tasdiqlash uchun **bulk action** yo'q (`is_active=True` qilish — hozir bittalab qo'lda)
- [ ] So'rovlar statusini o'zgartirish uchun action yo'q (pending → contacted → confirmed)
- [ ] Order'da `driver`, `client`, `tariff` uchun `raw_id_fields` / `autocomplete_fields` yo'q — 10 000 ta user bo'lsa admin sahifasi qotib qoladi
- [ ] `Payment` inline `Order` ichida ko'rinmaydi
- [ ] Admin sarlavhasi sozlanmagan (`admin.site.site_header = "SMART FLEET"`)
- [ ] `date_hierarchy` yo'q (sana bo'yicha filtrlash qulay bo'lardi)

### Admin API'da yetishmayotgan endpointlar

Agar alohida admin panel (frontend) qilinadigan bo'lsa, bular kerak:

```
GET    /api/admin/drivers/              # haydovchilar ro'yxati + filtr
PATCH  /api/admin/drivers/{id}/approve/ # haydovchini tasdiqlash (is_active)
PATCH  /api/admin/drivers/{id}/block/   # bloklash
GET    /api/admin/users/                # foydalanuvchilar ro'yxati
PATCH  /api/admin/users/{id}/block/     # user bloklash (is_active)
GET    /api/admin/orders/               # barcha buyurtmalar + filtr + pagination
PATCH  /api/admin/orders/{id}/cancel/   # admin buyurtmani bekor qiladi
GET    /api/admin/requests/heavy/       # og'ir texnika so'rovlari ro'yxati
GET    /api/admin/requests/wedding/     # to'y so'rovlari ro'yxati
PATCH  /api/admin/requests/{id}/status/ # so'rov statusini o'zgartirish
CRUD   /api/admin/tariffs/              # tarif qo'shish/o'zgartirish/o'chirish
GET    /api/admin/payments/             # to'lovlar ro'yxati
GET    /api/admin/stats/revenue/?from=&to=  # sana oralig'ida daromad
```

⚠️ **Muhim:** hozir og'ir texnika va to'y so'rovlarini **faqat POST qilish mumkin** — ularni ko'rish, statusini o'zgartirish uchun API umuman yo'q. Operator faqat email va Django admin orqali ishlaydi.

---

## 1. BLOKER — bularsiz loyiha ishlamaydi

- [ ] **`config/settings/base.py` yo'q.** `dev.py` va `prod.py` ikkalasi ham `from .base import *` qiladi. Ichida bo'lishi kerak: `INSTALLED_APPS`, `MIDDLEWARE`, `DATABASES` (PostGIS backend), `AUTH_USER_MODEL = "users.User"`, `AUTHENTICATION_BACKENDS` (PhoneBackend), `REST_FRAMEWORK` (JWT + `EXCEPTION_HANDLER` + `DEFAULT_PAGINATION_CLASS`), `SIMPLE_JWT`, `SPECTACULAR_SETTINGS`, `CORS_*`, Eskiz/Yandex/OSRM/Click/Email o'zgaruvchilari, `OTP_LENGTH`, `OTP_EXPIRE_SECONDS`, `STATIC_ROOT`, `MEDIA_ROOT`
- [ ] **Migration fayllari yo'q** — barcha `migrations/` papkalarida faqat `__init__.py`. `makemigrations` qilib, natijani git'ga qo'shish kerak
- [ ] `custom_exception_handler` `REST_FRAMEWORK` ga ulanganini tekshirish (base.py'da bo'lishi kerak edi)

---

## 2. Xavfsizlik (deploy'dan oldin shart)

- [ ] `ChangeStatusView` — egalik tekshiruvi yo'q, istalgan user begona buyurtma statusini o'zgartira oladi
- [ ] Mijoz `accepted` yuborsa unga Driver obyekti yaratiladi (`get_or_create_driver`)
- [ ] Click webhook'larida `amount` tekshirilmaydi → arzon narxda "to'lash" mumkin
- [ ] Click complete'da `merchant_prepare_id` tekshirilmaydi → prepare'siz to'lov o'tadi
- [ ] **Throttling umuman yo'q**: OTP yuborish, login, so'rov yuborish — hammasi cheksiz. DRF `ScopedRateThrottle` qo'shish kerak
- [ ] **Logout endpoint yo'q** — refresh token'ni bekor qilish imkoni yo'q. `rest_framework_simplejwt.token_blacklist` ulash kerak
- [ ] **Parolni o'zgartirish / tiklash endpointlari yo'q**
- [ ] Telefon raqam formati hech qayerda tekshirilmaydi (`+998XXXXXXXXX` regex kerak)
- [ ] lat/lng chegaralari tekshirilmaydi (-90..90 / -180..180)
- [ ] Click webhook'lariga IP whitelist yo'q

---

## 3. Yetishmayotgan funksionallik

README'da **Kun 5 va Kun 6 umuman yo'q** — o'sha bosqichlarda rejalashtirilgan narsalar qilinmagan ko'rinadi:

### 3.1 Reyting va sharhlar (ehtimol Kun 5)
- [ ] `Review` modeli yo'q. `Driver.rating` bor lekin **hech qachon yangilanmaydi** — hamma haydovchida abadiy 5.0
- [ ] `POST /api/orders/{id}/review/` — safar tugagach baho qoldirish
- [ ] Reytingni avtomatik qayta hisoblash
- [ ] Mijozni ham baholash (haydovchi tomonidan)

### 3.2 Bildirishnomalar (ehtimol Kun 6)
- [ ] **Real-time yo'q.** Haydovchi yangi buyurtmadan xabar topmaydi — `available/` ni qayta-qayta so'rab turishi kerak (polling)
- [ ] Mijoz haydovchi qabul qilganini bilmaydi
- [ ] Firebase push / WebSocket (Django Channels) — ikkalasi ham yo'q
- [ ] `Notification` modeli yo'q

### 3.3 Buyurtma bilan bog'liq
- [ ] **Buyurtmani haydovchiga avtomatik biriktirish yo'q** — eng yaqin haydovchini topib taklif qilish algoritmi kerak
- [ ] `available/` haydovchi joylashuvi bo'yicha filtrlamaydi
- [ ] Bekor qilish sababi (`cancel_reason`) saqlanmaydi
- [ ] Bekor qilganlik uchun jarima (cancellation fee) yo'q
- [ ] Safar davomida haydovchi lokatsiyasini kuzatish (tracking) endpoint'i yo'q
- [ ] Yakuniy narx faqat `estimated_price` ga teng — **haqiqiy masofa bo'yicha qayta hisoblanmaydi**
- [ ] Kutish vaqti uchun qo'shimcha to'lov yo'q
- [ ] Promo-kod / chegirma tizimi yo'q

### 3.4 To'lovlar
- [ ] **Payme integratsiyasi yo'q** — `PaymentMethod` da `payme` bor, lekin servis yozilmagan
- [ ] Naqd to'lovni tasdiqlash oqimi yo'q
- [ ] Pulni qaytarish (refund) yo'q
- [ ] Haydovchi hisobi / balansi / komissiya hisob-kitobi yo'q
- [ ] Haydovchining daromad statistikasi endpoint'i yo'q

### 3.5 Fayl va rasmlar
- [ ] Avatar faqat **URL** sifatida saqlanadi — rasm yuklash yo'q
- [ ] Haydovchi hujjatlari (guvohnoma, texpasport rasmi) yuklanmaydi — tasdiqlash real ishlamaydi
- [ ] Mashina rasmi yo'q
- [ ] `MEDIA_URL` sozlangan (`urls.py` da), lekin hech qanday `ImageField` yo'q

### 3.6 Boshqa
- [ ] `StandardPagination` yozilgan lekin **hech qayerda ishlatilmagan**
- [ ] `django-filter` o'rnatilgan lekin ishlatilmagan
- [ ] Ko'p tillilik yo'q — barcha xabarlar faqat o'zbekcha, hardcoded
- [ ] To'y narxi (125 000) kodda hardcoded — DB'ga ko'chirish kerak
- [ ] Og'ir texnika uchun narx hisoblash umuman yo'q

---

## 4. Testlar — 0%

- [ ] **Loyihada birorta ham test fayli yo'q** (`tests.py` hech bir app'da yo'q)
- [ ] Auth testlari (register, login, OTP)
- [ ] Status flow testlari (ruxsat etilgan/etilmagan o'tishlar)
- [ ] Narx hisoblash testlari (`calculate_price`, haversine fallback)
- [ ] Permission testlari (client/driver/admin)
- [ ] Click signature testlari
- [ ] `pytest-django` + `factory-boy` qo'shish
- [ ] Tashqi servislarni mock qilish (hozir testda ham real OSRM'ga chiqib ketadi)

---

## 5. Deploy (README'da "Kun 10 — qilinmagan")

Dockerfile va docker-compose **bor**, lekin to'liq emas:

- [ ] `docker-compose.yml` da `collectstatic` yo'q — prod'da whitenoise ishlatiladi, static yig'ilmasa admin panel **CSS'siz** ochiladi
- [ ] `SECRET_KEY`, `ALLOWED_HOSTS`, Click kalitlari compose'ga uzatilmagan — `env_file: .env` qo'shish kerak
- [ ] `db` uchun `healthcheck` yo'q, `web` migratsiyani DB tayyor bo'lishidan oldin boshlashi mumkin
- [ ] `restart: unless-stopped` yo'q
- [ ] **Nginx yo'q** (README'da va'da qilingan) — reverse proxy, SSL, static/media serving
- [ ] Static/media uchun volume yo'q — konteyner qayta ishga tushsa fayllar yo'qoladi
- [ ] `prod.py` da `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS` yo'q
- [ ] `prod.py` da `CORS_ALLOW_ALL_ORIGINS = False` qilingan, lekin `CORS_ALLOWED_ORIGINS` ro'yxati berilmagan → **frontend umuman ulana olmaydi**
- [ ] Sentry yoki xato monitoringi yo'q
- [ ] Logging sozlanmagan (fayl/rotatsiya)
- [ ] `.dockerignore` da `venv/` borligini tekshiring (image hajmi uchun)
- [ ] CI/CD yo'q (GitHub Actions)
- [ ] Backup strategiyasi yo'q

---

## 6. Infratuzilma yaxshilanishlari

- [ ] **Redis yo'q** — OTP kodlar DB'da saqlanadi (Redis TTL bilan ancha to'g'ri bo'lardi)
- [ ] **Celery yo'q** — SMS va email so'rov ichida sinxron yuboriladi. Eskiz sekin javob bersa foydalanuvchi kutadi. Navbatga o'tkazish kerak
- [ ] `nearby/` uchun kesh yo'q — har so'rovda PostGIS query
- [ ] Eskiz token'i xotirada saqlanadi (`self._token`) — bir nechta worker'da har biri alohida login qiladi, muddati tugasa yangilanmaydi (**bug**)
- [ ] OSRM public serveri ishlatilyapti — production uchun rate limit muammosi bo'ladi

---

## Ustuvorlik tartibi

**1-navbat (bugun):**
`base.py` yaratish → `makemigrations` → API'ni to'liq test qilish

**2-navbat (bu hafta):**
Xavfsizlik bug'lari (3, 4-bo'lim) → throttling → logout → testlar

**3-navbat:**
Reyting + bildirishnomalar + haydovchini avtomatik biriktirish → admin API

**4-navbat:**
Payme → fayl yuklash → deploy (nginx + collectstatic + env_file)
