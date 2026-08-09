// Backend +998XXXXXXXXX formatini talab qiladi, lekin serverda ham
// normalizatsiya bor. Foydalanuvchi qulayligi uchun mobil tarafda ham
// avtomatik +998 bilan boshlanadigan formatga keltiramiz.
export function normalizePhone(raw: string): string {
  const digits = raw.replace(/\D/g, '');
  if (digits.startsWith('998')) return `+${digits}`;
  if (digits.length === 9) return `+998${digits}`;
  if (digits.startsWith('0') && digits.length === 10) return `+998${digits.slice(1)}`;
  return `+${digits}`;
}

export function isValidUzPhone(raw: string): boolean {
  return /^\+998\d{9}$/.test(normalizePhone(raw));
}

export function formatPhoneDisplay(raw: string): string {
  const normalized = normalizePhone(raw);
  const match = normalized.match(/^\+998(\d{2})(\d{3})(\d{2})(\d{2})$/);
  if (!match) return normalized;
  return `+998 ${match[1]} ${match[2]} ${match[3]} ${match[4]}`;
}
