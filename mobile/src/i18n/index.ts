import uz, { TranslationKeys } from './locales/uz';
import ru from './locales/ru';
import en from './locales/en';

export type Language = 'uz' | 'ru' | 'en';

export const translations: Record<Language, TranslationKeys> = { uz, ru, en };

export const LANGUAGE_STORAGE_KEY = 'sf_language';

export const LANGUAGE_LABELS: Record<Language, string> = {
  uz: "O'zbekcha",
  ru: 'Русский',
  en: 'English',
};

// Obyekt ichidagi barcha "a.b.c" ko'rinishidagi yo'llarni chiqaradigan
// yordamchi tur — t('auth.login') kabi chaqiruvlarda avtomatik
// to'ldirish va xato-yo'l terishni ushlab qolish uchun.
type PathsOf<T, Prefix extends string = ''> = T extends string
  ? Prefix extends `${infer P}.`
    ? P
    : never
  : {
      [K in keyof T & string]: PathsOf<T[K], `${Prefix}${K}.`>;
    }[keyof T & string];

export type TranslationKey = PathsOf<TranslationKeys>;

function getByPath(obj: unknown, path: string): unknown {
  return path.split('.').reduce<unknown>((acc, part) => {
    if (acc && typeof acc === 'object' && part in (acc as Record<string, unknown>)) {
      return (acc as Record<string, unknown>)[part];
    }
    return undefined;
  }, obj);
}

export function translate(
  language: Language,
  key: TranslationKey,
  params?: Record<string, string | number>
): string {
  const dict = translations[language] ?? translations.uz;
  let value = getByPath(dict, key);
  if (typeof value !== 'string') {
    value = getByPath(translations.uz, key);
  }
  if (typeof value !== 'string') {
    return key;
  }
  if (!params) return value;
  return Object.keys(params).reduce(
    (str, paramKey) => str.replace(`{${paramKey}}`, String(params[paramKey])),
    value
  );
}
