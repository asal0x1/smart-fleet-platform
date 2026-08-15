// Backend manzili. Standart holatda production serveri ishlatiladi —
// shu sababli APK/IPA build qilinganda hech narsa sozlash shart emas
// (".env" fayli git'ga kirmaydi, EAS bulut build'iga ham yuborilmaydi).
//
// Lokal backend bilan ishlash uchun loyihaning ".env" fayliga
//   EXPO_PUBLIC_API_URL=http://192.168.x.x:8000
// qatorini yozing (namuna — ".env.example"). Expo'ning standart
// EXPO_PUBLIC_* mexanizmi bu qiymatni build vaqtida o'rniga qo'yadi.
const DEFAULT_ORIGIN = 'https://backend.smart-fleet.uz';

export const SERVER_ORIGIN = process.env.EXPO_PUBLIC_API_URL || DEFAULT_ORIGIN;
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
