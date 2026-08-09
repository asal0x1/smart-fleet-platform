// Backend manzili build-vaqtidagi environment o'zgaruvchisi orqali
// sozlanadi (Expo'ning standart EXPO_PUBLIC_* mexanizmi). Bu ilova
// serverga (production) qo'yilganda haqiqiy domenni ishlatishga, lokal
// rivojlantirishda esa hech narsa sozlamasdan ham ishlashga imkon beradi.
//
// Production uchun: loyihaning ".env" fayliga (yoki EAS build sirlariga)
//   EXPO_PUBLIC_API_URL=https://api.smartfleet.uz
// kabi qator qo'shing — namuna ".env.example" faylida ko'rsatilgan.
//
// Lokal rivojlantirish uchun hech narsa sozlash shart emas — pastdagi
// standart LAN IP ishlatiladi (agar kompyuterning IP manzili o'zgarsa,
// shu yerni yangilang: `ipconfig` — "IPv4-адрес" qatori).
const DEV_FALLBACK_ORIGIN = 'http://10.70.139.151:8000';

export const SERVER_ORIGIN = process.env.EXPO_PUBLIC_API_URL || DEV_FALLBACK_ORIGIN;
export const API_BASE_URL = `${SERVER_ORIGIN}/api`;
// http -> ws, https -> wss
export const WS_BASE_URL = `${SERVER_ORIGIN.replace(/^http/, 'ws')}/ws`;

// Ba'zi eski javoblarda rasm maydonlari (avatar, hujjatlar) to'liq URL
// o'rniga nisbiy yo'l (masalan "/media/avatars/x.jpg") qaytarishi mumkin —
// bunday holatda serverning asosiy manzilini oldiga qo'shib beramiz.
export function resolveMediaUrl(path?: string | null): string | null {
  if (!path) return null;
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  return `${SERVER_ORIGIN}${path.startsWith('/') ? '' : '/'}${path}`;
}
