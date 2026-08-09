import { Alert, Platform } from 'react-native';

export interface AlertButton {
  text?: string;
  style?: 'default' | 'cancel' | 'destructive';
  onPress?: () => void;
}

// react-native-web'ning Alert.alert() implementatsiyasi butunlay bo'sh
// (hech narsa qilmaydi) — shu sabab web'da barcha tasdiqlash/xatolik
// oynalari "ishlamay qolgan" bo'lib ko'rinardi (masalan "Chiqish"
// tugmasi bosilganda hech qanday dialog chiqmasdi). Bu yordamchi web'da
// brauzerning tabiiy confirm/alert oynalaridan foydalanib, xuddi shunday
// ishlaydi.
export function showAlert(title: string, message?: string, buttons?: AlertButton[]) {
  if (Platform.OS !== 'web') {
    Alert.alert(title, message, buttons as any);
    return;
  }

  const text = message ? `${title}\n\n${message}` : title;

  if (!buttons || buttons.length <= 1) {
    // eslint-disable-next-line no-alert
    window.alert(text);
    buttons?.[0]?.onPress?.();
    return;
  }

  const cancelButton = buttons.find((b) => b.style === 'cancel');
  const actionButton = buttons.find((b) => b !== cancelButton) ?? buttons[buttons.length - 1];

  // eslint-disable-next-line no-alert
  const confirmed = window.confirm(text);
  if (confirmed) {
    actionButton?.onPress?.();
  } else {
    cancelButton?.onPress?.();
  }
}
