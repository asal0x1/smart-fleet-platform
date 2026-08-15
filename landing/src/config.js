// Android ilovasi (APK) haqidagi ma'lumot — bir joyda saqlanadi.
//
// APK fayl repozitoriyada saqlanmaydi (86 MB) — u GitHub Releases
// orqali tarqatiladi va tugma to'g'ridan-to'g'ri o'sha faylga ishora
// qiladi. Shu sababli saytni deploy qilish uchun qo'shimcha ish yo'q.
//
// Yangi versiya chiqarganda:
//   1) yangi APK'ni release qilib yuklang:
//      gh release create v1.1.0 smart-fleet.apk --title "Smart Fleet 1.1.0"
//   2) quyidagi `version` va `size` qiymatlarini yangilang
//      (`url` ichidagi teg nomi ham o'zgaradi).
export const APK = {
  url: 'https://github.com/asal0x1/smart-fleet-platform/releases/download/v1.0.0/smart-fleet.apk',
  version: '1.0.0',
  size: '86 MB',
};
