import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';

// DIQQAT — Expo Go cheklovi:
// Bu yerda LOKAL bildirishnomalar ishlatiladi (ilova ochiq yoki fonda —
// lekin operatsion tizim tomonidan hali "o'ldirilmagan" holatda, JS
// jarayoni ishlab turganda WebSocket orqali xabar kelganda ko'rsatiladi).
// Ilova butunlay yopilgan (killed) holatda xabar olish uchun REAL push
// (Expo Push/FCM) kerak, bu esa Expo Go'da emas, faqat maxsus dev-build
// (EAS) orqali ishlaydi — SDK 53+ dan boshlab Expo Go remote push'ni
// Android'da qo'llab-quvvatlamaydi. Hozircha shu cheklov doirasida eng
// yaxshi mumkin bo'lgan yechim: lokal bildirishnoma.
let configured = false;

export function configureLocalNotifications() {
  if (configured) return;
  configured = true;
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: true,
      shouldSetBadge: false,
      shouldShowBanner: true,
      shouldShowList: true,
    }),
  });
}

export async function requestNotificationPermission(): Promise<boolean> {
  try {
    const { status } = await Notifications.getPermissionsAsync();
    if (status === 'granted') return true;
    const { status: requested } = await Notifications.requestPermissionsAsync();
    return requested === 'granted';
  } catch {
    return false;
  }
}

export async function presentLocalNotification(title: string, body: string) {
  try {
    // Web'da brauzer Notification ruxsati kerak, ruxsat bo'lmasa jim o'tamiz.
    if (Platform.OS === 'web') {
      const granted = await requestNotificationPermission();
      if (!granted) return;
    }
    await Notifications.scheduleNotificationAsync({
      content: { title, body, sound: true },
      trigger: null,
    });
  } catch {
    // Bildirishnoma ko'rsatilmasa ham asosiy oqim buzilmasligi kerak
  }
}
