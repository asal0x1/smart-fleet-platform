# SMART FLEET — Testlar (2-navbat)

Loyihada avval **birorta test yo'q edi**. Endi **279 ta test**, qamrov **93%**,
to'liq ishga tushish vaqti **~7 soniya**.

```
279 passed in 7.34s
TOTAL   1846 stmts   137 miss   93%
```

---

## O'rnatish

### 1. Fayllar

```
pytest.ini                      ← yangi
ruff.toml                       ← yangi
config/settings/test.py         ← yangi
requirements/dev.txt            ← almashtiriladi
.github/workflows/ci.yml        ← yangi

tests/__init__.py               ← yangi
tests/conftest.py               ← yangi (fixture'lar)
tests/factories.py              ← yangi (factory-boy)
tests/test_validators.py
tests/test_auth.py
tests/test_orders.py
tests/test_payments.py
tests/test_pricing.py
tests/test_throttling.py
tests/test_drivers_requests.py
tests/test_admin_api.py
```

Kichik lint tuzatishlari (CI birinchi kundan yashil bo'lishi uchun):
```
apps/common/admin_api/views.py  ← raise ... from exc
apps/users/serializers.py       ← raise ... from exc
apps/requests/views.py          ← ishlatilmagan import olib tashlandi
apps/orders/services.py         ← import tartibi
config/asgi.py, config/wsgi.py  ← import tartibi
```

### 2. Bog'liqliklar

```bash
pip install -r requirements/dev.txt
```

Qo'shildi: `pytest==8.2.2`, `pytest-django==4.8.0`, `pytest-cov==5.0.0`,
`factory-boy==3.3.0`.

> ⚠️ **Versiyalar pinlangan.** `pytest-django` ning eng yangi versiyasi
> (4.13) Django 4.2 bilan `AttributeError: PytestDjangoTestCase has no
> attribute '_pre_setup_ran_eagerly'` xatosini beradi. 4.8.0 barqaror.

### 3. Ishga tushirish

```bash
pytest                      # hammasi
pytest tests/test_auth.py   # bitta fayl
pytest -k "click"           # nom bo'yicha
pytest --create-db          # bazani qaytadan yaratish
pytest --cov=apps --cov=services --cov-report=term-missing
ruff check apps config services tests
```

`pytest.ini` da `--reuse-db` yoqilgan — test bazasi qayta ishlatiladi,
shuning uchun ikkinchi ishga tushirish ancha tez. Model o'zgartirsangiz
`--create-db` qo'shing.

---

## Tuzilma

| Fayl | Testlar | Nimani qamrab oladi |
|---|---|---|
| `test_admin_api.py` | 78 | 22 endpoint: ruxsat, filtr, action'lar |
| `test_orders.py` | 48 | status flow, egalik, buyurtma yaratish |
| `test_auth.py` | 35 | register, login, OTP, logout, parol |
| `test_payments.py` | 35 | Click: imzo, summa, prepare_id, idempotentlik |
| `test_drivers_requests.py` | 33 | profil, lokatsiya, nearby, so'rov formalari |
| `test_validators.py` | 25 | telefon normalizatsiya, koordinatalar |
| `test_pricing.py` | 15 | narx hisoblash, haversine, OSRM |
| `test_throttling.py` | 10 | rate limit cheklovlari |

---

## Muhim texnik qarorlar

### Tarmoq butunlay bloklangan

`conftest.py` dagi `block_network` fixture'i **autouse** — har testda
`requests.get` va `requests.post` bloklanadi.

Bu shunchaki tozalik uchun emas: 1-navbat ustida ishlaganda qo'lda
tekshiruvlar real OSRM serveriga chiqib ketardi va u `403` qaytarganda
natijalar tushunarsiz bo'lib qolardi. Endi `MapService.route()` xatoni
ushlab haversine fallback'ga o'tadi — masofa **deterministik** hisoblanadi.

OSRM'ning muvaffaqiyatli javobi alohida testda soxta `Response` bilan
tekshiriladi (`TestOSRMMuvaffaqiyatli`).

### Throttle cheklovini o'zgartirish

`settings.REST_FRAMEWORK` ni o'zgartirish **ishlamaydi**. Sababi:

```python
class SimpleRateThrottle(BaseThrottle):
    THROTTLE_RATES = api_settings.DEFAULT_THROTTLE_RATES   # ← havola
```

Bu sinf yaratilish paytida bir marta o'qiladi. `settings` fixture'i
`api_settings.reload()` ni chaqiradi, u **yangi dict** yasaydi, sinf esa
eskisiga ishora qilib qolaveradi. Shuning uchun `throttle_rate` fixture'i
sinf atributini to'g'ridan-to'g'ri almashtiradi.

Prod'ga ta'siri yo'q — u yerda settings bir marta yuklanadi.

### Test settings

`config/settings/test.py`:
- `MD5PasswordHasher` — PBKDF2 har user yaratishda ~300 ms yeydi.
  279 ta testda bu daqiqalarni tejaydi. **Faqat testda.**
- `locmem` email backend — `django.core.mail.outbox` orqali tekshiriladi
- `CLICK_SECRET_KEY = "test-secret"` — imzolar deterministik
- Migratsiyalar **o'chirilmagan**: ular ham test qilinishi kerak

### Fabrikalar

`DriverFactory` sukut bo'yicha **tasdiqlangan** haydovchi yaratadi,
`UnapprovedDriverFactory` esa tasdiqlanmagan. Ko'p test aynan shu
farqqa tayanadi, shuning uchun ikkitasi alohida.

---

## Nimalar tekshiriladi

**Xavfsizlik ssenariylari (1-navbatda tuzatilganlar):**
- begona mijoz buyurtma statusini o'zgartirishi → 403
- mijoz `accepted` yuborib haydovchiga aylanishi → 403, `Driver` yaratilmaydi
- tasdiqlanmagan haydovchi buyurtma qabul qilishi → 403
- ikki haydovchi bir buyurtmani olishi → 409
- 1000 so'mga 250 000 lik buyurtmani "to'lash" → `-2`
- prepare'siz to'g'ridan-to'g'ri complete → `-6`
- boshqa buyurtmaning `prepare_id` si → `-6`
- takroriy Click webhook → `-4`
- soxta imzo → `-1`
- to'langandan keyin "bekor qilish" holatni buzmasligi
- `+998...`, `998...`, `90 111 22 33` — bir xil raqam sifatida throttle qilinishi
- superuser va o'zini bloklashga urinish

**Biznes-mantiq:**
- status flow: 6 ta ruxsat etilgan, 6 ta taqiqlangan o'tish
- `minimum_fare` dan past narx chiqmasligi
- haversine simmetrikligi va nol masofa
- to'y so'rovi narxi (`car_count × duration_hours × 125 000`)
- izohlar ustiga qo'shilishi (o'chirilmasligi)
- ishlatilgan tarifning `PROTECT` sababli soft-delete bo'lishi

---

## CI

`.github/workflows/ci.yml` — har push va PR da:

1. PostGIS servisi ko'tariladi (`postgis/postgis:15-3.4`)
2. GDAL/PROJ tizim kutubxonalari o'rnatiladi
3. `makemigrations --check` — modelda o'zgarish bo'lib migratsiya
   yozilmagan bo'lsa CI yiqiladi
4. `manage.py check`
5. `pytest --cov-fail-under=80`
6. Alohida job'da `ruff check`

Hozirgi qamrov 93%, chegara 80% qilib qo'yildi — kod qo'shilganda biroz
tushishi normal, lekin 80 dan pastga tushsa CI ogohlantiradi.

---

## Qamrov taqsimoti

Yaxshi qamrab olingan:

| Modul | Qamrov |
|---|---|
| `apps/orders/services.py` | 100% |
| `apps/orders/serializers.py` | 100% |
| `apps/common/validators.py` | 100% |
| `apps/common/admin_api/filters.py` | 100% |
| `apps/requests/views.py` | 100% |
| `apps/users/views.py` | 99% |
| `apps/orders/views.py` | 98% |
| `apps/users/serializers.py` | 97% |
| `services/payment.py` | 95% |
| `apps/common/admin_api/views.py` | 91% |
| `apps/payments/views.py` | 91% |

Past qolganlar va sababi:

| Modul | Qamrov | Nega |
|---|---|---|
| `services/map.py` | 55% | Yandex geocoding hech qayerda ishlatilmaydi — o'lik kod |
| `services/sms.py` | 58% | real Eskiz integratsiyasi (mock rejimida ishlamaydi) |
| `apps/users/models.py` | 78% | `UserManager` ning ba'zi tarmoqlari |

> `services/map.py` dagi `geocode()` va `reverse_geocode()` metodlari
> loyihada **hech qayerda chaqirilmaydi**. Testlar shuni ochib berdi.
> Yo ularni ishlatish kerak (manzil bo'yicha qidiruv), yo o'chirish.

---

## Keyingi qadam

TODO bo'yicha **3-navbat** qoldi. Ichida eng muhimi — **fayl yuklash**
(`ImageField`): hozir haydovchi hujjatlari umuman yuklanmaydi, ya'ni
`approve/` tugmasi nimani tekshirib bosilishi noma'lum.

Reyting va real-time (Channels + Redis) undan keyin.
