# Smart Fleet

Monorepo: Smart Fleet transport va xizmatlar platformasi.

- `backend/` — Django REST API (JWT auth, orders, drivers, requests, WebSocket notifications)
- `mobile/` — Expo/React Native ilova (haydovchi va mijoz rollari, 6 ta xizmat moduli).
  Native (Expo Go) va veb ikkalasida ham ishlaydi.
- `landing/` — Marketing landing sahifasi (React + Vite),
  [smart-fleet-one-platform.vercel.app](https://smart-fleet-one-platform.vercel.app/)
  manzilida joylashtirilgan.

## Android ilovasi (APK)

Tayyor APK [Releases](https://github.com/asal0x1/smart-fleet-platform/releases)
bo'limida — fayl repozitoriyada saqlanmaydi (86 MB). Landing saytdagi
«Download the app» tugmasi to'g'ridan-to'g'ri o'sha faylga ishora qiladi,
manzil `landing/src/config.js` ichida.

Yangi versiya:

```
cd mobile
npx eas-cli build --platform android --profile preview
gh release create v1.1.0 smart-fleet.apk --title "Smart Fleet 1.1.0"
# so'ng landing/src/config.js dagi url / version / size yangilanadi
```

## Ishga tushirish

### Backend
```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements/dev.txt
copy .env.example .env   # va qiymatlarni to'ldiring
python manage.py migrate
python manage.py runserver
```

### Mobile
```
cd mobile
npm install
copy .env.example .env   # production uchun EXPO_PUBLIC_API_URL kiriting
npx expo start
```

### Landing
```
cd landing
npm install
npm run dev
```
