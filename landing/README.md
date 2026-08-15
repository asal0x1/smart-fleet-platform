# SmartFleet — landing

SmartFleet transport platformasining tanishtiruv sayti. Vite + React (JSX),
statik sayt — hech qanday backend talab qilmaydi.

## Ishga tushirish

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # natija: dist/
npm run preview    # yig'ilgan saytni tekshirish
```

## Deploy

`npm run build` `dist/` papkasini yaratadi — shu papkani statik sayt sifatida
joylashtirish kifoya.

### Nginx (VPS)

```nginx
server {
    listen 80;
    server_name smart-fleet.uz www.smart-fleet.uz;

    root /var/www/smartfleet-landing/dist;
    index index.html;

    # Bir sahifali ilova emas, lekin # havolalar uchun xavfsiz standart
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

Yangilash:

```bash
npm run build
rsync -avz --delete dist/ user@server:/var/www/smartfleet-landing/dist/
```

### Netlify / Vercel

- Build buyrug'i: `npm run build`
- Publish papkasi: `dist`

## Android ilovasi (APK)

APK fayl repozitoriyada saqlanmaydi (86 MB) — u
[GitHub Releases](../../releases) orqali tarqatiladi. Saytdagi «Download the
app» tugmasi to'g'ridan-to'g'ri release fayliga ishora qiladi, manzil bitta
joyda: [`src/config.js`](src/config.js).

Yangi versiya chiqarish:

```bash
gh release create v1.1.0 smart-fleet.apk --title "Smart Fleet 1.1.0"
# so'ng src/config.js dagi url / version / size yangilanadi
```

## Tuzilishi

```
src/
  components/     — sahifa bo'limlari (Hero, Services, FinalCTA, ...)
  assets/         — ilova skrinshotlari
  config.js       — APK havolasi va versiyasi
  index.css       — umumiy uslublar va CSS o'zgaruvchilari
```
