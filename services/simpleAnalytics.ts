import { Platform } from 'react-native';
import Constants from 'expo-constants';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Simple, lightweight analytics service that won't crash your app
export class SimpleAnalyticsService {
  private static isInitialized = false;
  private static events: any[] = [];

  static async initialize() {
    try {
      this.isInitialized = true;
      console.log('📊 Simple Analytics initialized');
      
      // Track app info
      const appInfo = {
        platform: Platform.OS,
        version: Platform.Version,
        appVersion: Constants.expoConfig?.version || '1.0.0',
        timestamp: Date.now(),
      };
      
      console.log('📱 App Info:', appInfo);
      
      // Load existing events
      await this.loadStoredEvents();
      
      return true;
    } catch (error) {
      console.log('Analytics initialization failed, but app will continue normally');
      return false;
    }
  }

  static async trackScreenView(screenName: string, screenClass?: string) {
    if (!this.isInitialized) return;
    
    const event = {
      type: 'screen_view',
      screen_name: screenName,
      screen_class: screenClass || screenName,
      timestamp: Date.now(),
    };
    
    console.log(`📱 Screen: ${screenName}`);
    await this.storeEvent(event);
  }

  static async trackEvent(eventName: string, parameters?: { [key: string]: any }) {
    if (!this.isInitialized) return;
    
    const event = {
      type: 'custom_event',
      event_name: eventName,
      parameters: parameters || {},
      timestamp: Date.now(),
    };
    
    console.log(`📊 Event: ${eventName}`, parameters);
    await this.storeEvent(event);
  }

  // News specific tracking
  static async trackNewsView(articleId: string, title: string, category: string, source: string) {
    await this.trackEvent('news_article_view', {
      article_id: articleId,
      title: title.substring(0, 100),
      category,
      source,
    });
  }

  static async trackNewsShare(articleId: string, shareMethod: string) {
    await this.trackEvent('news_article_share', {
      article_id: articleId,
      share_method: shareMethod,
    });
  }

  static async trackSearch(searchTerm: string, resultsCount: number) {
    await this.trackEvent('news_search', {
      search_term: searchTerm.substring(0, 50),
      results_count: resultsCount,
    });
  }

  static async trackBookmark(articleId: string, action: 'add' | 'remove') {
    await this.trackEvent('news_bookmark', {
      article_id: articleId,
      action,
    });
  }

  // App lifecycle events
  static async trackAppOpen() {
    await this.trackEvent('app_open', {
      platform: Platform.OS,
      app_version: Constants.expoConfig?.version,
    });
  }

  static async trackAppBackground() {
    await this.trackEvent('app_background');
  }

  static async trackFeatureUsage(feature: string, action: string) {
    await this.trackEvent('feature_usage', {
      feature_name: feature,
      action,
    });
  }

  static async trackUserEngagement(timeSpent: number, screenName: string) {
    await this.trackEvent('user_engagement', {
      engagement_time_msec: timeSpent,
      screen_name: screenName,
    });
  }

  static async trackError(error: string, context: string) {
    await this.trackEvent('app_error', {
      error_message: error.substring(0, 100),
      error_context: context,
    });
  }

  static async trackPerformance(action: string, duration: number) {
    await this.trackEvent('performance_metric', {
      action,
      duration_ms: duration,
    });
  }

  static async setUserProperties(properties: { [key: string]: string }) {
    if (!this.isInitialized) return;
    
    console.log('👤 User Properties:', properties);
    
    try {
      await AsyncStorage.setItem('@user_properties', JSON.stringify(properties));
    } catch (error) {
      console.log('Failed to store user properties');
    }
  }

  // Storage management
  private static async storeEvent(event: any) {
    try {
      this.events.push(event);
      
      // Keep only last 100 events
      if (this.events.length > 100) {
        this.events = this.events.slice(-100);
      }
      
      // Store events locally
      await AsyncStorage.setItem('@analytics_events', JSON.stringify(this.events));
      
      // Optional: Send to your backend periodically
      if (this.events.length % 10 === 0) {
        await this.syncEventsToBackend();
      }
    } catch (error) {
      // Silently fail - analytics shouldn't crash the app
    }
  }

  private static async loadStoredEvents() {
    try {
      const storedEvents = await AsyncStorage.getItem('@analytics_events');
      if (storedEvents) {
        this.events = JSON.parse(storedEvents);
      }
    } catch (error) {
      this.events = [];
    }
  }

  // Optional: Sync to your backend
  private static async syncEventsToBackend() {
    try {
      // Uncomment and configure if you have a backend endpoint
      /*
      await fetch('https://your-backend.com/analytics/batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          app_id: 'cyberx',
          platform: Platform.OS,
          events: this.events,
        }),
      });
      
      // Clear events after successful sync
      this.events = [];
      await AsyncStorage.removeItem('@analytics_events');
      */
      
      console.log(`📈 Analytics: ${this.events.length} events ready for sync`);
    } catch (error) {
      // Silently fail
    }
  }

  // Get analytics summary
  static async getAnalyticsSummary() {
    try {
      const userProperties = await AsyncStorage.getItem('@user_properties');
      return {
        totalEvents: this.events.length,
        recentEvents: this.events.slice(-5),
        userProperties: userProperties ? JSON.parse(userProperties) : {},
        isInitialized: this.isInitialized,
      };
    } catch (error) {
      return {
        totalEvents: 0,
        recentEvents: [],
        userProperties: {},
        isInitialized: this.isInitialized,
      };
    }
  }
}
