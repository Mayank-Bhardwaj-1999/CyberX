import { initializeApp } from 'firebase/app';
import Constants from 'expo-constants';
import { AnalyticsService } from './analyticsService';
import { FallbackAnalyticsService } from './fallbackAnalytics';

const firebaseConfig = {
  apiKey: Constants.expoConfig?.extra?.FIREBASE_API_KEY || '',
  authDomain: Constants.expoConfig?.extra?.FIREBASE_AUTH_DOMAIN || '',
  projectId: Constants.expoConfig?.extra?.FIREBASE_PROJECT_ID || '',
  storageBucket: Constants.expoConfig?.extra?.FIREBASE_STORAGE_BUCKET || '',
  messagingSenderId: Constants.expoConfig?.extra?.FIREBASE_MESSAGING_SENDER_ID || '',
  appId: Constants.expoConfig?.extra?.FIREBASE_APP_ID || '',
};

export const firebaseApp = initializeApp(firebaseConfig);

// Initialize Analytics with fallback
export const initializeFirebaseServices = async () => {
  try {
    const firebaseInitialized = await AnalyticsService.initialize();
    if (firebaseInitialized) {
      console.log('🔥 Firebase Analytics initialized successfully');
      return AnalyticsService;
    } else {
      throw new Error('Firebase Analytics failed to initialize');
    }
  } catch (error) {
    console.log('🔄 Using fallback analytics service');
    await FallbackAnalyticsService.initialize();
    return FallbackAnalyticsService;
  }
};

// Export the active analytics service
export let ActiveAnalyticsService: typeof AnalyticsService | typeof FallbackAnalyticsService = FallbackAnalyticsService;
