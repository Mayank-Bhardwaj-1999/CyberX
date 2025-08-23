import * as Notifications from 'expo-notifications';

// Configure notification handler
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

export async function sendBreakingNewsNotification(title: string, body: string) {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: `🚨 ${title}`,
      body,
      data: { type: 'breaking_news' },
      sound: 'default',
    },
    trigger: null,
  });
}

export async function sendGroupedNewsNotification(count: number, priority: 'normal' | 'high' = 'normal') {
  const title = getSmartTitle(count);
  const body = getSmartBody(count);
  const emoji = getSmartEmoji(count);

  await Notifications.scheduleNotificationAsync({
    content: {
      title: `${emoji} ${title}`,
      body,
      data: { 
        type: 'news_batch',  // Changed from 'news_update' to match backend
        count,
        priority,
        timestamp: new Date().toISOString(),
        grouped: true  // Indicates this is a batched notification
      },
      sound: priority === 'high' ? 'default' : undefined,
      badge: count,
    },
    trigger: null,
  });
  
  console.log(`🔔 Sent grouped notification: ${title} (${count} articles)`);
}

export async function sendSmartBatchNotification(notification: any) {
  /**
   * Send a pre-formatted batch notification from the backend
   */
  const { title, body, count, priority } = notification;
  
  await Notifications.scheduleNotificationAsync({
    content: {
      title: title || `📰 ${count} New Articles`,
      body: body || `${count} new cybersecurity articles available`,
      data: { 
        type: 'news_batch',
        count,
        priority,
        timestamp: notification.timestamp || new Date().toISOString(),
        grouped: true,
        source: 'backend'
      },
      sound: priority === 'high' ? 'default' : undefined,
      badge: count,
    },
    trigger: null,
  });
  
  console.log(`🔔 Sent smart batch notification: ${title} (${count} articles)`);
}

function getSmartTitle(count: number): string {
  if (count === 1) return 'New Security Alert';
  if (count <= 3) return `${count} New Articles`;
  if (count <= 10) return `${count} Security Updates`;
  return `Major Update: ${count} Articles`;
}

function getSmartBody(count: number): string {
  if (count === 1) return 'Critical cybersecurity news available';
  if (count <= 3) return `${count} new security articles to read`;
  if (count <= 10) return `${count} important updates available`;
  return `Comprehensive security update with ${count} new articles`;
}

function getSmartEmoji(count: number): string {
  if (count === 1) return '🔥';
  if (count <= 3) return '📰';
  if (count <= 10) return '🚨';
  return '⚡';
}

export async function sendDailyDigestNotification(articleCount: number) {
  await Notifications.scheduleNotificationAsync({
    content: {
      title: '📰 Daily News Digest',
      body: `${articleCount} new articles available to read`,
      data: { type: 'daily_digest' },
    },
    trigger: {
      type: 'calendar',
      hour: 9,
      minute: 0,
      repeats: true,
    } as Notifications.CalendarTriggerInput,
  });
}

// Smart notification polling service
class NotificationPollingService {
  private pollInterval: any = null;
  private isPolling = false;
  private lastNotificationTime = 0;
  private readonly POLL_INTERVAL = 30000; // 30 seconds
  private readonly MIN_NOTIFICATION_GAP = 60000; // 1 minute minimum between notifications

  async startPolling() {
    if (this.isPolling) return;
    
    this.isPolling = true;
    console.log('🔔 Starting notification polling service...');
    
    this.pollInterval = setInterval(() => {
      this.checkForNotifications();
    }, this.POLL_INTERVAL);

    // Check immediately
    this.checkForNotifications();
  }

  stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
    this.isPolling = false;
    console.log('🔕 Stopped notification polling service');
  }

  private async checkForNotifications() {
    try {
      // Simple fetch to avoid import issues
      const API_URL = process.env.EXPO_PUBLIC_API_URL || 'https://cyberx.icu';
      const response = await fetch(`${API_URL}/api/notifications`);
      const data = await response.json();

      if (data.status === 'success' && data.notifications.length > 0) {
        await this.processNotifications(data.notifications);
        
        // Clear notifications on server after processing
        await fetch(`${API_URL}/api/notifications?clear=true`);
      }
    } catch (error) {
      // Silently handle errors - API might not be available
      console.log('📡 API not available for notifications');
    }
  }

  private async processNotifications(notifications: any[]) {
    const now = Date.now();
    
    // Avoid notification spam - minimum 1 minute between notifications
    if (now - this.lastNotificationTime < this.MIN_NOTIFICATION_GAP) {
      console.log('⏳ Skipping notification - too soon after last one');
      return;
    }

    // Get the most recent notification
    const latestNotification = notifications[0];
    const count = latestNotification.count;
    const priority = latestNotification.priority || 'normal';
    const isGrouped = latestNotification.grouped || false;

    console.log(`🔔 Processing ${isGrouped ? 'grouped' : 'individual'} notification: ${count} articles, priority: ${priority}`);

    // Send appropriate notification based on type
    if (isGrouped) {
      // This is already a smart grouped notification from backend
      await sendSmartBatchNotification(latestNotification);
    } else {
      // Legacy individual notification - group it
      await sendGroupedNewsNotification(count, priority);
    }
    
    this.lastNotificationTime = now;
  }
}

// Export singleton instance
export const notificationService = new NotificationPollingService();

// Auto-start service
export async function initializeNotificationService() {
  try {
    // Request notification permissions
    const { status } = await Notifications.requestPermissionsAsync();
    
    if (status === 'granted') {
      console.log('✅ Notification permissions granted');
      
      // Start polling for notifications
      await notificationService.startPolling();
      
      return true;
    } else {
      console.log('❌ Notification permissions denied');
      return false;
    }
  } catch (error) {
    console.error('Error initializing notifications:', error);
    return false;
  }
}
