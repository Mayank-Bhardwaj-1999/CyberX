import * as Notifications from 'expo-notifications';
import { storage } from './storage';
import { NewsResponse, Article } from '../types/news';
import { getThreatLevel } from '../utils/threatAnalysis';

// Enhanced notification configuration
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

interface NotificationSettings {
  frequency: number; // in minutes: 60, 90, 120
  enabled: boolean;
  breakingNewsOnly: boolean;
  soundEnabled: boolean;
  vibrationEnabled: boolean;
  lastNotificationTime: number;
}

const DEFAULT_SETTINGS: NotificationSettings = {
  frequency: 30, // 30 minutes instead of 90 for more frequent notifications
  enabled: true,
  breakingNewsOnly: false,
  soundEnabled: true,
  vibrationEnabled: true,
  lastNotificationTime: 0,
};

const SETTINGS_KEY = 'enhanced_notification_settings';
const SEEN_ARTICLES_KEY = 'seen_articles_for_notifications';

class EnhancedNotificationService {
  private static instance: EnhancedNotificationService;
  private settings: NotificationSettings = DEFAULT_SETTINGS;
  private seenArticles: Set<string> = new Set();
  private monitoringInterval?: ReturnType<typeof setInterval>;

  static getInstance(): EnhancedNotificationService {
    if (!EnhancedNotificationService.instance) {
      EnhancedNotificationService.instance = new EnhancedNotificationService();
    }
    return EnhancedNotificationService.instance;
  }

  async initialize() {
    await this.loadSettings();
    await this.loadSeenArticles();
    this.startMonitoring();
  }

  private async loadSettings() {
    try {
      const stored = await storage.getItem(SETTINGS_KEY);
      if (stored) {
        this.settings = { ...DEFAULT_SETTINGS, ...JSON.parse(stored) };
      }
    } catch (error) {
      console.error('Error loading notification settings:', error);
    }
  }

  private async saveSettings() {
    try {
      await storage.setItem(SETTINGS_KEY, JSON.stringify(this.settings));
    } catch (error) {
      console.error('Error saving notification settings:', error);
    }
  }

  private async loadSeenArticles() {
    try {
      const stored = await storage.getItem(SEEN_ARTICLES_KEY);
      if (stored) {
        this.seenArticles = new Set(JSON.parse(stored));
      }
    } catch (error) {
      console.error('Error loading seen articles:', error);
    }
  }

  private async saveSeenArticles() {
    try {
      await storage.setItem(SEEN_ARTICLES_KEY, JSON.stringify(Array.from(this.seenArticles)));
    } catch (error) {
      console.error('Error saving seen articles:', error);
    }
  }

  private startMonitoring() {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
    }

    // Check every 30 seconds but respect user's frequency setting
    this.monitoringInterval = setInterval(() => {
      this.checkForNewArticles();
    }, 30000);
  }

  private async checkForNewArticles() {
    if (!this.settings.enabled) return;

    const now = Date.now();
    const timeSinceLastNotification = now - this.settings.lastNotificationTime;
    const frequencyMs = this.settings.frequency * 60 * 1000;

    // Don't send notifications too frequently
    if (timeSinceLastNotification < frequencyMs) {
      return;
    }

    try {
      // Fetch recent articles from backend
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_URL || 'https://cyberx.icu'}/api/news`);
      if (!response.ok) {
        return; // Backend not available
      }
      
      const data = await response.json() as NewsResponse;
      
      if (data.articles && data.articles.length > 0) {
        const newArticles = data.articles.filter(article => 
          !this.seenArticles.has(article.url) && 
          this.isRecentArticle(article)
        );

        if (newArticles.length > 0) {
          // Filter for breaking news if setting is enabled
          const articlesToNotify = this.settings.breakingNewsOnly 
            ? newArticles.filter(article => this.isBreakingNews(article))
            : newArticles;

          if (articlesToNotify.length > 0) {
            await this.sendEnhancedNotification(articlesToNotify);
            
            // Mark articles as seen
            articlesToNotify.forEach(article => {
              this.seenArticles.add(article.url);
            });
            
            // Clean up old seen articles (keep only last 1000)
            if (this.seenArticles.size > 1000) {
              const articlesArray = Array.from(this.seenArticles);
              this.seenArticles = new Set(articlesArray.slice(-800));
            }
            
            await this.saveSeenArticles();
            this.settings.lastNotificationTime = now;
            await this.saveSettings();
          }
        }
      }
    } catch (error) {
      console.log('Enhanced notification check failed - API might be offline');
    }
  }

  private isRecentArticle(article: Article): boolean {
    if (!article.publishedAt) return true; // Assume recent if no timestamp
    
    const articleTime = new Date(article.publishedAt).getTime();
    const now = Date.now();
    const twoHoursMs = 2 * 60 * 60 * 1000; // 2 hours
    
    return (now - articleTime) < twoHoursMs;
  }

  private isBreakingNews(article: Article): boolean {
    const title = article.title.toLowerCase();
    const description = (article.description || '').toLowerCase();
    
    const breakingKeywords = [
      'breaking', 'urgent', 'alert', 'critical', 'emergency',
      'hack', 'breach', 'attack', 'vulnerability', 'exploit',
      'malware', 'ransomware', 'phishing', 'zero-day',
      'data breach', 'cyber attack', 'security incident'
    ];
    
    return breakingKeywords.some(keyword => 
      title.includes(keyword) || description.includes(keyword)
    );
  }

  private async sendEnhancedNotification(articles: Article[]) {
    try {
      const count = articles.length;
      const firstArticle = articles[0];
      
      // Analyze threat level
      const threatLevel = getThreatLevel(firstArticle);
      
      // Create attractive notification content
      const { title, body, sound } = this.createNotificationContent(count, threatLevel, firstArticle);
      
      await Notifications.scheduleNotificationAsync({
        content: {
          title,
          body,
          data: { 
            type: 'enhanced_news',
            articleCount: count,
            threatLevel,
            articles: articles.slice(0, 3).map(a => ({
              title: a.title,
              url: a.url,
              source: a.source.name
            }))
          },
          sound: this.settings.soundEnabled ? sound : undefined,
          badge: count,
        },
        trigger: null,
      });

      console.log(`🔔 Enhanced notification sent: ${title}`);
    } catch (error) {
      console.error('Error sending enhanced notification:', error);
    }
  }

  private createNotificationContent(count: number, threatLevel: string, firstArticle: Article) {
    let emoji = '📰';
    let sound: 'default' | 'defaultCritical' = 'default';
    let title = '';
    let body = '';

    // Choose emoji and sound based on threat level
    switch (threatLevel) {
      case 'critical':
        emoji = '🚨';
        sound = 'defaultCritical';
        break;
      case 'high':
        emoji = '⚠️';
        sound = 'defaultCritical';
        break;
      case 'medium':
        emoji = '🔔';
        break;
      case 'low':
        emoji = '📰';
        break;
    }

    // Create engaging titles based on content and threat level
    if (count === 1) {
      if (threatLevel === 'critical' || threatLevel === 'high') {
        title = `${emoji} URGENT: Security Alert`;
        body = firstArticle.title.substring(0, 100) + '...';
      } else {
        title = `${emoji} Breaking Cybersecurity News`;
        body = firstArticle.title.substring(0, 100) + '...';
      }
    } else {
      const threats = ['critical', 'high'].includes(threatLevel);
      if (threats) {
        title = `${emoji} ${count} CRITICAL Security Updates`;
        body = `Multiple high-priority threats detected including: ${firstArticle.title.substring(0, 50)}...`;
      } else {
        title = `${emoji} ${count} New Security Stories`;
        body = `Latest cybersecurity news including: ${firstArticle.title.substring(0, 60)}...`;
      }
    }

    // Add call-to-action phrases
    const actionPhrases = [
      'Tap to read now',
      'Stay protected',
      'Update your defenses',
      'Check details',
      'Read more'
    ];
    
    const randomAction = actionPhrases[Math.floor(Math.random() * actionPhrases.length)];
    body += ` • ${randomAction}`;

    return { title, body, sound };
  }

  // Public API methods
  async updateSettings(newSettings: Partial<NotificationSettings>) {
    this.settings = { ...this.settings, ...newSettings };
    await this.saveSettings();
    
    // Restart monitoring if frequency changed
    if (newSettings.frequency || newSettings.enabled !== undefined) {
      this.startMonitoring();
    }
  }

  getSettings(): NotificationSettings {
    return { ...this.settings };
  }

  async testNotification() {
    try {
      await Notifications.scheduleNotificationAsync({
        content: {
          title: '🔔 CyberX Notifications Active',
          body: 'You will receive security updates every ' + this.settings.frequency + ' minutes',
          data: { type: 'test' },
        },
        trigger: null,
      });
    } catch (error) {
      console.error('Error sending test notification:', error);
    }
  }

  stopMonitoring() {
    if (this.monitoringInterval) {
      clearInterval(this.monitoringInterval);
      this.monitoringInterval = undefined;
    }
  }
}

// Export singleton instance
export const enhancedNotificationService = EnhancedNotificationService.getInstance();

// Hook for using enhanced notifications
export function useEnhancedNotifications() {
  return {
    updateSettings: (settings: Partial<NotificationSettings>) => 
      enhancedNotificationService.updateSettings(settings),
    getSettings: () => enhancedNotificationService.getSettings(),
    testNotification: () => enhancedNotificationService.testNotification(),
    initialize: () => enhancedNotificationService.initialize(),
  };
}

export default EnhancedNotificationService;
