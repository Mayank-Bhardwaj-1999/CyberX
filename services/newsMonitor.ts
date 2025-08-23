import { useNotifications } from '../store/NotificationContext';
import { api } from './api';
import { NewsResponse, Article } from '../types/news';
import { sendGroupedNewsNotification, sendSmartBatchNotification } from './notifications';

let lastArticleCount = 0;
let isMonitoring = false;
let lastMonitorTime = 0;
let lastAlertCheckTime = 0;
const MONITOR_COOLDOWN = 60000; // 1 minute cooldown
const ALERT_CHECK_INTERVAL = 30000; // Check for alerts every 30 seconds

export async function startNewsMonitoring() {
  if (isMonitoring) return;
  
  isMonitoring = true;
  console.log('🚀 Starting news monitoring with alert system');
  
  // Check for new articles every 2 minutes
  const interval = setInterval(async () => {
    const now = Date.now();
    if (now - lastMonitorTime < MONITOR_COOLDOWN) {
      return; // Skip if called too frequently
    }
    lastMonitorTime = now;

    try {
      console.log('🔔 Checking for new articles...');
      const data = await api.listNews(1, 1) as NewsResponse;
      
      if (data.articles && data.articles.length > 0) {
        const currentCount = data.totalResults || data.articles.length;
        
        // If we have more articles than before, add notifications
        if (currentCount > lastArticleCount && lastArticleCount > 0) {
          const newCount = currentCount - lastArticleCount;
          console.log(`📧 New articles detected: ${newCount}`);
          
          // Send notification using the notification service
          await sendGroupedNewsNotification(newCount, newCount > 5 ? 'high' : 'normal');
        }
        
        lastArticleCount = currentCount;
      }
    } catch (error) {
      console.log('📡 API not available for news monitoring');
    }
  }, 120000); // Check every 2 minutes
  
  // Check for alerts from the backend file watcher system
  const alertInterval = setInterval(async () => {
    const now = Date.now();
    if (now - lastAlertCheckTime < ALERT_CHECK_INTERVAL) {
      return;
    }
    lastAlertCheckTime = now;
    
    await checkForAlerts();
  }, ALERT_CHECK_INTERVAL);
  
  return () => {
    clearInterval(interval);
    clearInterval(alertInterval);
    isMonitoring = false;
  };
}

async function checkForAlerts() {
  try {
    // Poll the backend for new notifications from the file watcher
    const response = await fetch(`${process.env.EXPO_PUBLIC_API_URL || 'https://cyberx.icu'}/api/notifications`);
    
    if (!response.ok) {
      return; // Silently fail if backend is not available
    }
    
    const data = await response.json();
    
    if (data.notifications && data.notifications.length > 0) {
      // Send each notification using the notification service
      for (const notification of data.notifications) {
        await sendSmartBatchNotification(notification);
      }
      
      // Clear the notifications after processing
      await fetch(`${process.env.EXPO_PUBLIC_API_URL || 'https://cyberx.icu'}/api/notifications?clear=true`);
      
      console.log(`🔔 Processed ${data.notifications.length} alerts from file watcher`);
    }
    
  } catch (error) {
    // Silently handle errors - backend might not be available
    console.log('📡 Alert polling failed - backend might be offline');
  }
}

export function useNewsMonitor() {
  const { addNotification } = useNotifications();
  
  const checkForNewArticles = async () => {
    const now = Date.now();
    if (now - lastMonitorTime < MONITOR_COOLDOWN) {
      return; // Skip if called too frequently
    }
    lastMonitorTime = now;

    try {
      const data = await api.listNews(1, 5) as NewsResponse;
      
      if (data.articles && data.articles.length > 0) {
        const currentCount = data.totalResults || data.articles.length;
        
        if (currentCount > lastArticleCount && lastArticleCount > 0) {
          const newArticlesCount = Math.min(currentCount - lastArticleCount, data.articles.length);
          const newArticles: Article[] = data.articles.slice(0, newArticlesCount);
          
          newArticles.forEach((article) => {
            addNotification({
              title: 'New Cybersecurity Alert',
              source: article.source?.name || 'CyberX News',
              timestamp: Date.now(),
            });
          });
          
          console.log(`📧 Added ${newArticles.length} new article notifications`);
        }
        
        lastArticleCount = currentCount;
      }
    } catch (error) {
      console.log('📡 Failed to check for new articles');
      // Don't spam error logs for monitoring
    }
  };

  const getAlertStats = async () => {
    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_URL || 'https://cyberx.icu'}/api/alerts/stats`);
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.log('Failed to fetch alert stats');
    }
    return null;
  };

  const getRecentAlerts = async (page = 1, limit = 20, unreadOnly = false) => {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: limit.toString(),
        unread_only: unreadOnly.toString()
      });
      
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_URL || 'https://cyberx.icu'}/api/alerts?${params}`);
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.log('Failed to fetch recent alerts');
    }
    return null;
  };

  const markAlertsAsRead = async (alertIds: string[] = [], markAll = false) => {
    try {
      const response = await fetch(`${process.env.EXPO_PUBLIC_API_URL || 'https://cyberx.icu'}/api/alerts/mark-read`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ alert_ids: alertIds, mark_all: markAll })
      });
      
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.log('Failed to mark alerts as read');
    }
    return null;
  };

  return { 
    checkForNewArticles, 
    getAlertStats, 
    getRecentAlerts, 
    markAlertsAsRead 
  };
}
