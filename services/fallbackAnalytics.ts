import { Platform } from 'react-native';
import Constants from 'expo-constants';

// Fallback analytics for development and compatibility
export class FallbackAnalyticsService {
  
  static async initialize() {
    console.log('📊 Fallback Analytics initialized');
    console.log('Device Info:', {
      platform: Platform.OS,
      version: Platform.Version,
      appVersion: Constants.expoConfig?.version,
      buildNumber: Constants.expoConfig?.android?.versionCode,
    });
    return true;
  }

  static async trackScreenView(screenName: string, screenClass?: string) {
    console.log(`📱 Screen: ${screenName} (${screenClass || 'N/A'})`);
    
    // Send to your backend analytics endpoint if available
    this.sendToBackend('screen_view', {
      screen_name: screenName,
      screen_class: screenClass || screenName,
      timestamp: Date.now(),
    });
  }

  static async trackEvent(eventName: string, parameters?: { [key: string]: any }) {
    console.log(`📊 Event: ${eventName}`, parameters);
    
    // Send to your backend analytics endpoint if available
    this.sendToBackend('custom_event', {
      event_name: eventName,
      ...parameters,
      timestamp: Date.now(),
    });
  }

  // News specific events
  static async trackNewsView(articleId: string, title: string, category: string, source: string) {
    await this.trackEvent('news_article_view', {
      article_id: articleId,
      article_title: title.substring(0, 100),
      category: category,
      news_source: source,
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
      action: action,
    });
  }

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
      action: action,
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
      action: action,
      duration_ms: duration,
    });
  }

  static async setUserProperties(properties: { [key: string]: string }) {
    console.log('👤 User Properties:', properties);
    
    // Store user properties locally for now
    this.sendToBackend('user_properties', {
      properties,
      timestamp: Date.now(),
    });
  }

  // Send analytics data to your backend (optional)
  private static async sendToBackend(eventType: string, data: any) {
    try {
      // Uncomment and configure if you have a backend analytics endpoint
      /*
      await fetch('https://your-backend.com/analytics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_type: eventType,
          data: data,
          app_id: 'cyberx',
          user_agent: Platform.OS,
        }),
      });
      */
      
      // For now, just store locally or log
      console.log(`🔄 Analytics Event: ${eventType}`, data);
    } catch (error) {
      console.log('Analytics backend unavailable');
    }
  }
}
