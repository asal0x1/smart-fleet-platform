import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import AsyncStorage from '@react-native-async-storage/async-storage';

const ACCESS_KEY = 'sf_access_token';
const REFRESH_KEY = 'sf_refresh_token';

// expo-secure-store'ning web'da hech qanday implementatsiyasi yo'q
// (native Keychain/Keystore'ga mos veb-analog mavjud emas), shuning uchun
// veb'da AsyncStorage (localStorage asosida) ishlatiladi. Nativeda esa
// shifrlangan SecureStore saqlanadi.
const backend = Platform.OS === 'web'
  ? {
      getItem: (key: string) => AsyncStorage.getItem(key),
      setItem: (key: string, value: string) => AsyncStorage.setItem(key, value),
      deleteItem: (key: string) => AsyncStorage.removeItem(key),
    }
  : {
      getItem: (key: string) => SecureStore.getItemAsync(key),
      setItem: (key: string, value: string) => SecureStore.setItemAsync(key, value),
      deleteItem: (key: string) => SecureStore.deleteItemAsync(key),
    };

export const tokenStorage = {
  async getAccess() {
    return backend.getItem(ACCESS_KEY);
  },
  async getRefresh() {
    return backend.getItem(REFRESH_KEY);
  },
  async setTokens(access: string, refresh: string) {
    await backend.setItem(ACCESS_KEY, access);
    await backend.setItem(REFRESH_KEY, refresh);
  },
  async setAccess(access: string) {
    await backend.setItem(ACCESS_KEY, access);
  },
  async clear() {
    await backend.deleteItem(ACCESS_KEY);
    await backend.deleteItem(REFRESH_KEY);
  },
};
