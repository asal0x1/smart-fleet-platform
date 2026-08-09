# Smart Fleet

Monorepo: Smart Fleet transport va xizmatlar platformasi.

- `backend/` — Django REST API (JWT auth, orders, drivers, requests, WebSocket notifications)
- `mobile/` — Expo/React Native ilova (haydovchi va mijoz rollari, 6 ta xizmat moduli).
  Native (Expo Go) va veb ikkalasida ham ishlaydi — veb versiyasi
  [smart-fleet-one-platform.vercel.app](https://smart-fleet-one-platform.vercel.app/)
  manzilida joylashtirilgan (`expo export --platform web` orqali).

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
