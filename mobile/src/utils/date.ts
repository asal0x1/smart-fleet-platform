// DIQQAT: Date.prototype.toISOString() UTC vaqtidan foydalanadi.
// Toshkent UTC+5 bo'lgani uchun (yoki UTC'dan oldinda turgan har qanday
// zona uchun) mahalliy yarim tunni ISO-ga aylantirsangiz sana BIR KUNGA
// ORQAGA suriladi (masalan 9-avgust tanlansa "2026-08-08" yuboriladi).
// Backendga har doim shu — mahalliy sana bo'yicha — funksiyadan foydalanib
// yuborish kerak, toISOString() emas.
export function formatDateForApi(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}
