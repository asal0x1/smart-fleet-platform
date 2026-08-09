import { Platform } from 'react-native';

function guessMimeType(ext: string) {
  const e = ext.toLowerCase();
  if (e === 'jpg' || e === 'jpeg') return 'image/jpeg';
  if (e === 'png') return 'image/png';
  if (e === 'webp') return 'image/webp';
  return `image/${e}`;
}

function extensionFromMimeType(mimeType: string): string {
  const map: Record<string, string> = {
    'image/jpeg': 'jpg',
    'image/jpg': 'jpg',
    'image/png': 'png',
    'image/webp': 'webp',
    'image/heic': 'heic',
  };
  return map[mimeType.toLowerCase()] ?? 'jpg';
}

// React Native'da fayl {uri, name, type} shaklida FormData'ga qo'shiladi
// (native bridge shu formatni URI orqali o'qiydi). Brauzerning haqiqiy
// FormData API'si esa buni tushunmaydi — u haqiqiy Blob/File talab qiladi.
// Shu sabab web'da URI'ni fetch qilib, Blob'ga aylantiramiz.
export async function appendFileToFormData(form: FormData, field: string, uri: string) {
  if (Platform.OS === 'web') {
    const response = await fetch(uri);
    const blob = await response.blob();
    // MUHIM: expo-image-picker web'da URL.createObjectURL() orqali
    // "blob:http://localhost:8081/<uuid>" ko'rinishidagi URI beradi —
    // bunda kengaytma UMUMAN yo'q. Agar shu UUID'ni fayl nomi sifatida
    // yuborsak, Django ImageField "kengaytma ruxsat etilmagan" deb 400
    // qaytaradi. Shuning uchun kengaytmani URI'dan emas, Blob'ning
    // haqiqiy MIME turidan (blob.type) aniqlaymiz.
    const ext = extensionFromMimeType(blob.type || 'image/jpeg');
    const filename = `${field}.${ext}`;
    form.append(field, blob, filename);
    return;
  }

  const rawName = uri.split('/').pop()?.split('?')[0] || `${field}.jpg`;
  const match = /\.(\w+)$/.exec(rawName);
  const ext = match ? match[1] : 'jpg';
  const mimeType = guessMimeType(ext);
  form.append(field, {
    uri,
    name: rawName,
    type: mimeType,
  } as unknown as Blob);
}

// Web'da 'multipart/form-data' headerini qo'lda qo'yish xato — chegara
// (boundary) parametrisiz yuborilib, server multipart body'ni o'qiy olmay
// qoladi. Brauzer buni FormData'dan avtomatik to'g'ri hosil qiladi, shuning
// uchun web'da Content-Type header umuman berilmasligi kerak; nativeda esa
// aniq header kerak.
export function multipartHeaders(): Record<string, string> | undefined {
  return Platform.OS === 'web' ? undefined : { 'Content-Type': 'multipart/form-data' };
}
