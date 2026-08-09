# SMART FLEET — Django admin (5-navbat)

TODO'ning 5-navbatidagi barcha punktlar + qo'shimchalar.
**46 ta yangi test**, jami **325 ta test**, qamrov **93%**.

---

## O'rnatish

### Yangi fayllar
```
apps/common/admin.py            ← site branding (Django avtomatik yuklaydi)
apps/common/admin_mixins.py     ← admin_link, boolean_icon, StatusColorMixin
tests/test_admin_site.py        ← 46 ta test
```

### Almashtiriladigan
```
apps/users/admin.py
apps/drivers/admin.py
apps/orders/admin.py
apps/payments/admin.py
apps/requests/admin.py
```

Migratsiya kerak emas — faqat admin qatlami o'zgardi.

```bash
python manage.py check
python manage.py runserver     # /admin/
```

---

## Nima qo'shildi

### 1. Bulk action'lar — eng katta vaqt tejash

**Haydovchilar:**
| Action | Nima qiladi |
|---|---|
| Tanlanganlarni TASDIQLASH | `is_active=True` + `user.is_verified=True` |
| Tasdiqni BEKOR QILISH | `is_active=False` + majburan offline |
| Majburan OFFLINE | faqat `is_online=False`, tasdiqqa tegmaydi |

Tasdiqlash **mashina raqami bo'sh** haydovchini o'tkazib yuboradi va
qaysilari o'tkazilganini xabar qilib aytadi. Sababi: raqamsiz haydovchi
buyurtma olsa, mijoz qaysi mashinani kutayotganini bilmaydi.

**Foydalanuvchilar:** BLOKLASH, blokdan CHIQARISH, telefonni TASDIQLANGAN
deb belgilash. Bloklash **o'zini va superuser'ni** chetlab o'tadi —
aks holda admin o'z hisobidan chiqib qolishi mumkin.

**So'rovlar:** BOG'LANILDI / TASDIQLANDI / YAKUNLANDI / BEKOR QILINDI.
Operator kuniga o'nlab so'rov ko'radi; har birini ochib, status tanlab,
saqlash juda sekin edi.

**Buyurtmalar:** bulk bekor qilish. Yakunlangan/bekor qilinganlarga
tegmaydi va nechtasi o'tkazib yuborilganini aytadi. Kutilayotgan
`Payment`lar ham avtomatik `cancelled` bo'ladi.

### 2. `autocomplete_fields`

`Order` da `client`, `driver`, `tariff`; `Driver` da `user`;
`Payment` da `order`.

Ilgari oddiy `<select>` ishlatilardi — 10 000 ta foydalanuvchi bo'lsa
Django har bir buyurtma sahifasida hammasini HTML'ga chiqarardi va
sahifa amalda ochilmay qolardi. Endi AJAX qidiruv.

> Buning ishlashi uchun **manba admin'da `search_fields` bo'lishi shart**.
> Shu sababli `TariffAdmin` ga ham `search_fields` qo'shildi.

### 3. `PaymentInline`

To'lovlar endi buyurtma sahifasining ichida ko'rinadi. Ilgari operator
to'lov holatini tekshirish uchun alohida bo'limga o'tib, buyurtma
raqamini qidirishi kerak edi.

### 4. Ko'rinish

- `site_header` / `site_title` / `index_title` → "SMART FLEET"
- Rangli status nishonlari (`StatusColorMixin`) — kutmoqda sariq,
  yakunlangan yashil, bekor qilingan qizil
- Bog'langan obyektlarga havolalar (mijoz → user sahifasi,
  haydovchi → driver sahifasi)
- `date_hierarchy` barcha asosiy modellarda
- `list_per_page = 50`
- Narxlar bo'sh joy bilan ajratiladi: `250 000`
- `Driver` ro'yxatida buyurtmalar soni, `User` da ham

### 5. N+1 so'rovlar yopildi

Barcha `get_queryset()` da `select_related` va kerakli `annotate`.
Ilgari 50 qatorli haydovchilar ro'yxati 50+ ta qo'shimcha SQL so'rov
yasardi (har qator uchun `user`).

### 6. Yangi filtr

`ApprovalFilter` — "Tasdiq kutmoqda / Tasdiqlangan / Hisobi bloklangan".
Tasdiq kutayotganlarni bir bosishda ko'rish uchun; `is_active` va
`user.is_active` farqini oddiy filtr ko'rsata olmasdi.

### 7. Himoyalar

- `Payment` qo'lda qo'shilmaydi (`has_add_permission = False`) —
  to'lov faqat Click webhook orqali yaratilishi kerak
- `OTPCode` qo'shilmaydi va tahrirlanmaydi — faqat ko'rish
- To'lovlar ro'yxati sarlavhasida **filtrga mos** umumiy va to'langan
  summa ko'rsatiladi

---

## Test natijasi

```
325 passed in 5.31s
TOTAL   2126 stmts   139 miss   93%
ruff: All checks passed!
```

`tests/test_admin_site.py` — 46 ta test:
- 8 ta modelning changelist sahifasi ochilishi
- 5 ta autocomplete endpoint javob berishi
- har bir bulk action'ning haqiqiy natijasi
- mashina raqamisiz haydovchi o'tkazib yuborilishi
- o'zini va superuser'ni bloklab bo'lmasligi
- yakunlangan buyurtmaga tegilmasligi
- admin orqali yaratilgan user parolining hash qilinishi
- `Payment` va `OTPCode` qo'shish taqiqlangani
- to'lovlar sarlavhasidagi yig'indi

---

## Yo'l-yo'lakay topilgan narsa

`django.contrib.gis.admin` da `SimpleListFilter` **yo'q** — u faqat
`django.contrib.admin` da. GIS admin ishlatilgan modullarda ikkalasini
ham import qilish kerak:

```python
from django.contrib import admin as base_admin
from django.contrib.gis import admin
```

---

## Admin panelga oid nima qoldi

1. **Audit log** — kim qaysi haydovchini bloklaganini yozib boruvchi model.
   Bulk action'lar qo'shilgach bu yanada muhimroq bo'ldi: bir bosishda
   50 ta hisobni bloklash mumkin, izi esa qolmaydi.
2. **Hujjat rasmlari** (3-navbat) — `ImageField` hali yo'q, ya'ni
   "TASDIQLASH" tugmasi nimani tekshirib bosilishi noma'lumligicha qolyapti.
   Bu 5-navbatdagi ishning qiymatini cheklaydi.
3. **Nginx** (4-navbat) — usiz prod'da admin panel static fayllari
   to'g'ri berilmaydi.
