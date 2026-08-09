# SMART FLEET — Qolgan ishlar (yangilangan: 06.08.2026, 2-navbat yakunlandi)

> Bu fayl eski `TODO_QOLGAN_ISHLAR.md` o'rniga. Eskisidagi ikkita punkt
> noto'g'ri edi: `config/settings/base.py` **bor** va migratsiya fayllari ham
> **bor**. Ular "BLOKER" ro'yxatidan olib tashlandi.

---

## ✅ Tayyor

| Bo'lim | Holat |
|---|---|
| Settings (base/dev/prod) | ✅ |
| Migratsiyalar | ✅ barcha app'da |
| Auth (register, login, OTP, JWT, profile) | ✅ |
| Orders (tarif, narx, status flow) | ✅ |
| Drivers (profil, lokatsiya, PostGIS nearby) | ✅ |
| Payments — Click prepare/complete | ✅ (lekin xavfsizlik teshigi bor, pastga qarang) |
| Requests — og'ir texnika + to'y (POST + email) | ✅ |
| Django admin — 8 model | ✅ |
| **Admin API — 22 endpoint** | ✅ 06.08.2026 |
| **CORS + CSRF + docker env_file** | ✅ 06.08.2026 |
| **1-navbat: xavfsizlik (15 punkt)** | ✅ 06.08.2026 |
| **2-navbat: testlar — 279 ta, 93% qamrov** | ✅ 06.08.2026 |
| **CI (GitHub Actions) + ruff** | ✅ 06.08.2026 |
| **5-navbat: Django admin qulayliklari** | ✅ 06.08.2026 |
| **3-navbat: fayl yuklash, reyting, masofa filtri** | ✅ 06.08.2026 |
| **MVP: WebSocket, geocode, yakuniy narx, naqd to'lov** | ✅ 06.08.2026 |
| `StandardPagination` ishlatilishi | ✅ |
| `django-filter` ishlatilishi | ✅ |
| `Order.cancel_reason` | ✅ |

---

## ✅ 1-NAVBAT — Xavfsizlik (BAJARILDI)

Har biri real zarar keltiradi. Taxminan **2–3 kun**.

### 1.1 Buyurtma egaligi tekshirilmaydi ⚠️ eng katta teshik
- [ ] `ChangeStatusView` (`apps/orders/views.py`) — istalgan foydalanuvchi begona
      buyurtma statusini o'zgartira oladi. `OrderDetailView.get_object()` da
      allaqachon to'g'ri mantiq bor — o'shani `ChangeStatusView` ga ham qo'llash kerak.
- [ ] Mijoz `accepted` yuborsa unga `get_or_create_driver()` orqali Driver obyekti
      yaratiladi — mijoz haydovchiga aylanadi. `IsDriver` tekshiruvi qo'yish kerak.
- [ ] `get_or_create_driver()` ni umuman `get_or_404` ga o'zgartirish — haydovchi
      profili ro'yxatdan o'tishda yaratilishi kerak, tasodifan emas.

### 1.2 Click to'lovi
- [ ] **`amount` tekshirilmaydi** → 1 so'mga "to'lash" mumkin.
      `CLICK_INVALID_AMOUNT` (-2) konstantasi yozilgan, lekin hech qayerda ishlatilmagan.
- [ ] **`merchant_prepare_id` tekshirilmaydi** → prepare bosqichisiz to'lov o'tadi.
- [ ] Click webhook'lariga IP whitelist yo'q.
- [ ] Idempotentlik: bir xil `click_trans_id` ikki marta kelsa nima bo'ladi — tekshirilmagan.

### 1.3 Throttling — umuman yo'q
Kodda birorta `throttle` so'zi yo'q. Eng xavflisi — **OTP yuborish cheksiz**:
bitta skript Eskiz hisobingizni bir kechada bo'shatib yuboradi.
- [ ] `REST_FRAMEWORK` ga `DEFAULT_THROTTLE_CLASSES` + `ScopedRateThrottle`
- [ ] `send-otp/` → 3/soat bir telefon raqamga
- [ ] `login/`, `register/` → 10/soat bir IP'ga
- [ ] `heavy-equipment/requests/`, `wedding/requests/` → 5/soat

### 1.4 Auth
- [ ] **Logout yo'q** — `rest_framework_simplejwt.token_blacklist` ulanmagan.
      `INSTALLED_APPS` ga qo'shish + `BLACKLIST_AFTER_ROTATION = True` + migratsiya.
- [ ] Parol o'zgartirish endpoint'i yo'q
- [ ] Parol tiklash (OTP orqali) yo'q

### 1.5 Validatsiya
- [ ] Telefon formati hech qayerda tekshirilmaydi — `+998XXXXXXXXX` regex validator
      yozib, `User.phone` va barcha `contact_phone` maydonlariga qo'llash
- [ ] lat/lng chegaralari tekshirilmaydi (-90..90 / -180..180) — `CreateOrderSerializer`,
      `EstimateSerializer`, `LocationUpdateSerializer`, `nearby/` da
- [ ] `radius` chegarasi yo'q — `nearby/?radius=99999999` bazani qotiradi

### 1.6 Django admin
- [ ] `UserAdmin` oddiy `ModelAdmin` — parol xeshi ochiq ko'rinadi va admin'dan
      user yaratib bo'lmaydi (parol hash qilinmaydi). `BaseUserAdmin` ga o'tkazish.

---

## ✅ 2-NAVBAT — Testlar (BAJARILDI — 279 ta, 93%)

Loyihada **birorta test fayli yo'q**. Taxminan **2–3 kun**.

- [ ] `pytest-django` + `factory-boy` + `pytest-cov` o'rnatish, `pytest.ini`
- [ ] `conftest.py` — user/driver/order/tariff fabrikalari
- [ ] Tashqi servislarni mock qilish — **hozir test ham real OSRM'ga chiqib ketadi**
- [ ] Auth testlari (register, login, OTP, muddati o'tgan kod)
- [ ] Status flow testlari — ruxsat etilgan va etilmagan o'tishlar
- [ ] Permission testlari — client / driver / admin, begona buyurtma
- [ ] Narx hisoblash testlari (`calculate_price`, haversine fallback)
- [ ] Click imzo va `amount` testlari
- [ ] Admin API testlari (22 endpoint uchun kamida permission + filtr)

Natija: **279 ta test, 93% qamrov, ~7 soniya.** Maqsad 60% edi.

---

## 🟡 3-NAVBAT — Yetishmayotgan funksionallik

README'dagi **Kun 5 va Kun 6 umuman qilinmagan**. Taxminan **1–2 hafta**.

### 3.1 Reyting va sharhlar (Kun 5)
- [ ] `Review` modeli yo'q — `Driver.rating` hech qachon yangilanmaydi,
      hamma haydovchida abadiy 5.0
- [ ] `POST /api/orders/{id}/review/` — safar tugagach baho
- [ ] Reytingni avtomatik qayta hisoblash (signal yoki servis)
- [ ] Mijozni ham baholash (haydovchi tomonidan)

### 3.2 Bildirishnomalar (Kun 6)
- [ ] **Real-time yo'q** — haydovchi `available/` ni polling qiladi
- [ ] Mijoz haydovchi qabul qilganini bilmaydi
- [ ] Django Channels + Redis **yoki** Firebase push — ikkalasi ham yo'q
- [ ] `Notification` modeli yo'q

> Bu eng katta bo'lak. WebSocket'ni tanlasangiz Redis ham kerak bo'ladi (6-bo'lim).

### 3.3 Buyurtma
- [ ] Avtomatik haydovchi biriktirish yo'q — eng yaqin haydovchini topib taklif
      qilish algoritmi. (Admin API'da **qo'lda** biriktirish endi bor.)
- [ ] `available/` haydovchi joylashuvi bo'yicha filtrlamaydi — Toshkentdagi haydovchi
      Samarqand buyurtmasini ko'radi
- [ ] Yakuniy narx = `estimated_price`, haqiqiy masofa bo'yicha qayta hisoblanmaydi
- [ ] Kutish vaqti uchun qo'shimcha to'lov yo'q
- [ ] Bekor qilganlik uchun jarima yo'q
- [ ] Promo-kod / chegirma tizimi yo'q

### 3.4 To'lovlar
- [ ] Payme yo'q — `PaymentMethod` da bor, servis yozilmagan
- [ ] Naqd to'lovni tasdiqlash oqimi yo'q
- [ ] Refund yo'q
- [ ] Haydovchi balansi / komissiya hisob-kitobi yo'q
      (daromad statistikasi admin API'da qisman bor)

### 3.5 Fayl va rasmlar
- [ ] **Loyihada birorta `ImageField` yo'q** — ya'ni:
- [ ] Avatar faqat URL sifatida saqlanadi, yuklash yo'q
- [ ] Haydovchi hujjatlari (guvohnoma, texpasport) yuklanmaydi →
      **tasdiqlash real ishlamaydi**, admin nimani tekshiradi?
- [ ] Mashina rasmi yo'q
- [ ] `MEDIA_URL` sozlangan, lekin ishlatilmaydi

### 3.6 Boshqa
- [ ] Ko'p tillilik yo'q — barcha xabarlar hardcoded o'zbekcha
- [ ] To'y narxi (125 000) kodda hardcoded — DB'ga ko'chirish
- [ ] Og'ir texnika uchun narx hisoblash umuman yo'q

---

## 🟡 4-NAVBAT — Deploy (Kun 10)

Taxminan **2–3 kun**.

- [ ] **Nginx yo'q** — reverse proxy, SSL (Let's Encrypt), static/media serving
- [ ] SSL o'rnatgach `.env` da `SECURE_SSL_REDIRECT=True`, `SECURE_HSTS_SECONDS=31536000`
      (kod tayyor, faqat yoqish qoldi)
- [ ] `.dockerignore` da `venv/` borligini tekshirish
- [ ] Sentry yoki xato monitoringi yo'q
- [ ] Logging sozlanmagan (fayl + rotatsiya)
- [x] ~~CI/CD (GitHub Actions: lint + test)~~ ✅ bajarildi
- [ ] Backup strategiyasi yo'q (`pg_dump` cron)

✅ Bajarilgan: `env_file`, `collectstatic`, `healthcheck`, `restart`, volume'lar, CORS.

---

## ✅ 5-NAVBAT — Django admin qulayliklari (BAJARILDI)

Kichik ishlar, har biri 10–20 daqiqa.

- [x] ~~Haydovchini tasdiqlash uchun bulk action~~ ✅ (+ bekor qilish, offline)
- [x] ~~So'rov statusini o'zgartirish action'i~~ ✅ (4 ta status)
- [x] ~~`Order` da `autocomplete_fields`~~ ✅ (client, driver, tariff)
- [x] ~~`Payment` ni `Order` ichida inline~~ ✅
- [x] ~~`admin.site.site_header`~~ ✅
- [x] ~~`date_hierarchy`~~ ✅
- [x] Qo'shimcha: user bloklash action'lari, N+1 so'rovlar, rangli statuslar,
      tasdiq filtri, Payment/OTPCode qo'shishni taqiqlash
- [ ] **Audit log** — kim qaysi haydovchini bloklaganini yozib borish
      (bulk action'lar qo'shilgach yanada muhimroq: bir bosishda 50 ta
      hisobni bloklash mumkin, izi qolmaydi)

---

## 🟢 6-NAVBAT — Infratuzilma

- [ ] **Redis yo'q** — OTP kodlar DB'da (Redis TTL bilan ancha to'g'ri)
- [ ] **Celery yo'q** — SMS va email so'rov ichida sinxron yuboriladi;
      Eskiz sekin javob bersa foydalanuvchi kutib turadi
- [ ] **Eskiz token bug'i** — token `self._token` da xotirada saqlanadi.
      Bir nechta gunicorn worker'da har biri alohida login qiladi, muddati
      tugasa yangilanmaydi. Redis'ga ko'chirish kerak.
- [ ] `nearby/` uchun kesh yo'q — har so'rovda PostGIS query
- [ ] OSRM public serveri — prod'da rate limit muammosi bo'ladi

---

## Tavsiya etilgan tartib

| # | Ish | Taxminiy vaqt |
|---|---|---|
| ~~1~~ | ~~Xavfsizlik (1-navbat)~~ | ✅ bajarildi |
| ~~2~~ | ~~Testlar (2-navbat)~~ | ✅ bajarildi |
| ~~5~~ | ~~Django admin qulayliklari~~ | ✅ bajarildi |
| 3 | Fayl yuklash (3.5) — tasdiqlash ishlashi uchun | 1–2 kun |
| 4 | Reyting (3.1) | 2 kun |
| 5 | Bildirishnomalar (3.2) — Channels + Redis | 4–6 kun |
| 6 | Deploy: nginx + SSL + Sentry | 2–3 kun |
| 7 | Payme, promo-kod, avtomatik biriktirish | 1 hafta+ |

**Jami 1–6 uchun: ~3 hafta.** Ustiga 20–30% zaxira qo'shing — WebSocket va
to'lov mantig'i har doim rejadan uzoqroq cho'ziladi.

Agar maqsad "tezroq ishlaydigan MVP" bo'lsa: **1 → 3 → 6** yetadi,
reyting va real-time'ni keyinga qoldirsa bo'ladi.


---

## 2-navbat davomida topilgan yangi narsa

`services/map.py` dagi `geocode()` va `reverse_geocode()` metodlari
loyihada **hech qayerda chaqirilmaydi** (shuning uchun qamrov 55%).
Yandex API kaliti ham `.env` da bor. Ikki yo'l:
- manzil bo'yicha qidiruvni frontend'ga ochish (foydali funksiya), yoki
- o'lik kodni o'chirish

Shuningdek `Order.tariff` uchun `raw_id_fields` hali qo'yilmagan (5-navbat).


---

# YAKUNIY HOLAT (06.08.2026)

Backend **MVP darajasida tayyor**. 410 test, 93% qamrov.

## Qolgan ishlar — faqat ikki turkum

### Infratuzilma (kodda emas)
- [ ] Nginx + SSL (Let's Encrypt). `/ws/` uchun `proxy_set_header Upgrade`
      sozlamasi shart — usiz WebSocket ulanishi uziladi
- [ ] Sentry, logging, `pg_dump` backup cron

### Birinchi mijozlardan keyin
- [ ] Payme (Click ishlayapti)
- [ ] Promo-kod, refund, kutish to'lovi, bekor qilish jarimasi
- [ ] Haydovchi balansi va komissiya
- [ ] Ko'p tillilik
- [ ] Audit log
- [ ] Celery (SMS hozir sinxron, ~1 soniya)
- [ ] Avtomatik haydovchi biriktirish (hozir e'lon hammaga ketadi,
      birinchi qabul qilgan oladi — MVP uchun yetarli)

Bularni oldindan qilish tavsiya etilmaydi: real ehtiyoj aniqlanmaguncha
ishlatilmaydigan kod bo'lib qolishi mumkin.

## Endi frontend

Tavsiya etilgan tartib:
1. Admin panel (2–3 hafta) — API 100% tayyor
2. Landing + so'rov formalari (3–5 kun)
3. Haydovchi ilovasi (3–4 hafta)
4. Mijoz ilovasi (4–6 hafta)
