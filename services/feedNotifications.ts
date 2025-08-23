import * as Notifications from 'expo-notifications';
import * as Linking from 'expo-linking';
import { Article, NewsResponse } from '../types/news';
import { storage } from './storage';

const FEED_NOTIFICATION_KEY = 'last_feed_check';
const NOTIFICATION_COOLDOWN = 30 * 60 * 1000; // 30 minutes between notifications

// Configure notification handler for feed notifications
Notifications.setNotificationHandler({
  handleNotification: async (notification) => {
    const data = notification.request.content.data;
    
    return {
      shouldShowAlert: true,
      shouldPlaySound: data?.priority === 'high',
      shouldSetBadge: true,
      shouldShowBanner: true,
      shouldShowList: true,
    };
  },
});

export interface FeedNotificationData {
  type: 'feed_article';
  articleUrl: string;
  articleId?: string;
  source: string;
  category: string;
  timestamp: string;
  priority: 'normal' | 'high';
}

class FeedPushNotificationService {
  private isMonitoring = false;
  private lastCheckTime = 0;
  private addNotification: any = null;

  // Initialize the service
  async initialize() {
    try {
      // Request permissions
      const { status } = await Notifications.requestPermissionsAsync();
      if (status !== 'granted') {
        console.log('❌ Push notification permissions denied');
        return false;
      }

      // Set up notification response listener for deep linking
      this.setupNotificationResponseListener();
      
      // Start monitoring feed for new articles
      this.startFeedMonitoring();
      
      console.log('🚀 Feed push notifications initialized successfully');
      return true;
    } catch (error) {
      console.error('Error initializing feed notifications:', error);
      return false;
    }
  }

  // Set up deep linking when notifications are tapped
  private setupNotificationResponseListener() {
    Notifications.addNotificationResponseReceivedListener(response => {
      const data = response.notification.request.content.data as unknown as FeedNotificationData;
      
      if (data?.type === 'feed_article' && data.articleUrl) {
        // Create deep link to open the article
        this.openArticleFromNotification(data);
      }
    });
  }

  // Open article when notification is tapped
  private async openArticleFromNotification(data: FeedNotificationData) {
    try {
      // Store the article data temporarily for the app to access
      await storage.setItem('notification_article', JSON.stringify({
        url: data.articleUrl,
        source: data.source,
        category: data.category,
        timestamp: data.timestamp,
        fromNotification: true
      }));

      // Create deep link URL - this will open the article view
      const url = `cyberx://article?url=${encodeURIComponent(data.articleUrl)}`;
      await Linking.openURL(url);
      
      console.log('📱 Opening article from notification:', data.source);
    } catch (error) {
      console.error('Error opening article from notification:', error);
    }
  }

  // Start monitoring feed for new articles
  private async startFeedMonitoring() {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    console.log('📡 Starting feed monitoring for push notifications...');

    // Check every 30 minutes for new articles
    const checkInterval = setInterval(async () => {
      await this.checkForNewFeedArticles();
    }, 30 * 60 * 1000); // 30 minutes

    // Also do an initial check after 2 minutes
    setTimeout(() => {
      this.checkForNewFeedArticles();
    }, 2 * 60 * 1000);

    return checkInterval;
  }

  // Check for new feed articles and send notifications
  private async checkForNewFeedArticles() {
    try {
      const now = Date.now();
      const lastCheck = await storage.getItem(FEED_NOTIFICATION_KEY);
      const lastCheckTime = lastCheck ? parseInt(lastCheck) : now - (24 * 60 * 60 * 1000); // 24 hours ago if no previous check

      // Avoid too frequent checks
      if (now - this.lastCheckTime < NOTIFICATION_COOLDOWN) {
        console.log('⏳ Feed notification cooldown active, skipping check');
        return;
      }
      
      this.lastCheckTime = now;
      console.log('🔍 Checking for new feed articles...');

      // Get latest articles from API using same pattern as useNews hook
      const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'https://cyberx.icu';
      const response = await fetch(`${API_BASE_URL}/api/news?page=1&limit=10`);
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data?.articles && data.articles.length > 0) {
        // Filter articles newer than last check
        const newArticles = data.articles.filter((article: Article) => {
          const articleTime = new Date(article.publishedAt).getTime();
          return articleTime > lastCheckTime;
        });

        if (newArticles.length > 0) {
          console.log(`📧 Found ${newArticles.length} new articles for feed notifications`);
          
          // Send notifications for new articles (max 3 to avoid spam)
          const articlesToNotify = newArticles.slice(0, 3);
          
          for (const article of articlesToNotify) {
            await this.sendFeedArticleNotification(article);
          }
          
          // Update last check time
          await storage.setItem(FEED_NOTIFICATION_KEY, now.toString());
        } else {
          console.log('📭 No new articles found for notifications');
        }
      }
    } catch (error: any) {
      console.log('📡 Failed to check for new feed articles:', error?.message || 'Unknown error');
    }
  }

  // Send push notification for a new feed article
  private async sendFeedArticleNotification(article: Article) {
    try {
      const priority = this.determineArticlePriority(article);
      const { title, body, emoji } = this.createNotificationContent(article, priority);
      
      const notificationData: FeedNotificationData = {
        type: 'feed_article',
        articleUrl: article.url,
        articleId: article.url, // Using URL as ID
        source: article.source.name,
        category: this.extractCategory(article),
        timestamp: new Date().toISOString(),
        priority
      };

      // Send the push notification
      await Notifications.scheduleNotificationAsync({
        content: {
          title: `${emoji} ${title}`,
          body: body,
          data: notificationData as any, // Type assertion for notification data
          sound: priority === 'high' ? 'default' : undefined,
          badge: 1,
        },
        trigger: null, // Send immediately
      });

      // Also add to internal notification system
      if (this.addNotification) {
        this.addNotification({
          id: Date.now().toString(),
          type: 'news' as const,
          title: title,
          description: body,
          source: article.source.name,
          timestamp: new Date(),
          read: false,
          articleUrl: article.url
        });
      }

      console.log(`🔔 Sent feed notification: ${title}`);
    } catch (error) {
      console.error('Error sending feed notification:', error);
    }
  }

  // Determine article priority based on keywords and source
  private determineArticlePriority(article: Article): 'normal' | 'high' {
    const content = `${article.title} ${article.description}`.toLowerCase();
    
    const highPriorityKeywords = [
      'breaking', 'urgent', 'critical', 'zero-day', 'ransomware', 
      'data breach', 'hack', 'cyber attack', 'vulnerability',
      'security alert', 'malware', 'phishing'
    ];

    const hasHighPriorityKeyword = highPriorityKeywords.some(keyword => 
      content.includes(keyword)
    );

    const highPrioritySources = [
      'bleepingcomputer', 'krebs', 'threatpost', 'darkreading'
    ];

    const isHighPrioritySource = highPrioritySources.some(source => 
      article.source.name.toLowerCase().includes(source)
    );

    return hasHighPriorityKeyword || isHighPrioritySource ? 'high' : 'normal';
  }

  // Create engaging notification content
  private createNotificationContent(article: Article, priority: 'normal' | 'high') {
    const source = article.source.name;
    const titleWords = article.title.split(' ').slice(0, 8).join(' ');
    const descWords = article.description ? article.description.split(' ').slice(0, 12).join(' ') : '';
    
    let emoji = '🛡️';
    let title = '';
    
    if (priority === 'high') {
      emoji = '🚨';
      title = `Breaking: ${titleWords}`;
    } else {
      const content = article.title.toLowerCase();
      if (content.includes('breach')) emoji = '💥';
      else if (content.includes('ransomware')) emoji = '🔒';
      else if (content.includes('malware')) emoji = '🦠';
      else if (content.includes('vulnerability')) emoji = '⚠️';
      else if (content.includes('hack')) emoji = '💻';
      
      title = `New: ${titleWords}`;
    }

    const body = descWords ? `${descWords}... • ${source}` : `Latest from ${source}`;

    return { title, body, emoji };
  }

  // Extract article category for organization
  private extractCategory(article: Article): string {
    const content = `${article.title} ${article.description}`.toLowerCase();
    
    if (content.includes('breach') || content.includes('leak')) return 'Data Breach';
    if (content.includes('ransomware')) return 'Ransomware';
    if (content.includes('malware') || content.includes('virus')) return 'Malware';
    if (content.includes('vulnerability') || content.includes('cve')) return 'Vulnerability';
    if (content.includes('phishing') || content.includes('scam')) return 'Phishing';
    if (content.includes('apt') || content.includes('attack')) return 'Cyber Attack';
    
    return 'Security News';
  }

  // Set notification context for adding to internal system
  setNotificationContext(addNotificationFn: any) {
    this.addNotification = addNotificationFn;
  }

  // Manual trigger for testing
  async sendTestNotification() {
    const testArticle: Article = {
      title: "Test Security Alert: New Vulnerability Discovered",
      description: "This is a test notification to verify the feed notification system is working correctly.",
      summary: "Test notification summary",
      url: "https://example.com/test-article",
      urlToImage: null,
      publishedAt: new Date().toISOString(),
      source: { id: "test", name: "CyberX Test" },
      author: "Test Author",
      content: "Test content"
    };

    await this.sendFeedArticleNotification(testArticle);
  }
}

export const feedPushNotificationService = new FeedPushNotificationService();
