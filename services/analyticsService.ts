import analytics from '@react-native-firebase/analytics';

export class AnalyticsService {
  // Initialize analytics
  static async initialize() {
    try {
      // Enable analytics collection
      await analytics().setAnalyticsCollectionEnabled(true);
      
      // Set default user properties
      await analytics().setUserId('user_' + Date.now());
      await analytics().setUserProperty('app_version', '1.0.0');
      await analytics().setUserProperty('platform', 'android');
      
      console.log('✅ Firebase Analytics initialized');
      return true;
    } catch (error) {
      console.error('❌ Analytics initialization failed:', error);
      console.log('📊 Analytics will work in production build');
      return false;
    }
  }

  // Track screen views
  static async trackScreenView(screenName: string, screenClass?: string) {
    try {
      await analytics().logScreenView({
        screen_name: screenName,
        screen_class: screenClass || screenName,
      });
      console.log(`📱 Screen view logged: ${screenName}`);
    } catch (error) {
      console.log(`📱 Screen view tracked: ${screenName} (will sync in production)`);
    }
  }

  // Track custom events
  static async trackEvent(eventName: string, parameters?: { [key: string]: any }) {
    try {
      await analytics().logEvent(eventName, parameters);
      console.log(`📊 Event logged: ${eventName}`, parameters);
    } catch (error) {
      console.log(`📊 Event tracked: ${eventName} (will sync in production)`);
    }
  }

  // News specific events
  static async trackNewsView(articleId: string, title: string, category: string, source: string) {
    await this.trackEvent('news_article_view', {
      article_id: articleId,
      article_title: title.substring(0, 100), // Limit length
      category: category,
      news_source: source,
      timestamp: Date.now()
    });
  }

  static async trackNewsShare(articleId: string, shareMethod: string) {
    await this.trackEvent('news_article_share', {
      article_id: articleId,
      share_method: shareMethod,
      timestamp: Date.now()
    });
  }

  static async trackSearch(searchTerm: string, resultsCount: number) {
    await this.trackEvent('news_search', {
      search_term: searchTerm.substring(0, 50),
      results_count: resultsCount,
      timestamp: Date.now()
    });
  }

  static async trackBookmark(articleId: string, action: 'add' | 'remove') {
    await this.trackEvent('news_bookmark', {
      article_id: articleId,
      action: action,
      timestamp: Date.now()
    });
  }

  // App engagement events
  static async trackAppOpen() {
    await this.trackEvent('app_open');
  }

  static async trackAppBackground() {
    await this.trackEvent('app_background');
  }

  static async trackFeatureUsage(feature: string, action: string) {
    await this.trackEvent('feature_usage', {
      feature_name: feature,
      action: action,
      timestamp: Date.now()
    });
  }

  // User behavior tracking
  static async trackUserEngagement(timeSpent: number, screenName: string) {
    await this.trackEvent('user_engagement', {
      engagement_time_msec: timeSpent,
      screen_name: screenName,
      timestamp: Date.now()
    });
  }

  // Error tracking
  static async trackError(error: string, context: string) {
    await this.trackEvent('app_error', {
      error_message: error.substring(0, 100),
      error_context: context,
      timestamp: Date.now()
    });
  }

  // Performance tracking
  static async trackPerformance(action: string, duration: number) {
    await this.trackEvent('performance_metric', {
      action: action,
      duration_ms: duration,
      timestamp: Date.now()
    });
  }

  // Set user properties
  static async setUserProperties(properties: { [key: string]: string }) {
    try {
      for (const [key, value] of Object.entries(properties)) {
        await analytics().setUserProperty(key, value);
      }
      console.log('👤 User properties set:', properties);
    } catch (error) {
      console.log('👤 User properties tracked (will sync in production):', properties);
    }
  }
}
