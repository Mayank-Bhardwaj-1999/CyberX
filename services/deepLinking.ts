import * as Linking from 'expo-linking';
import { router } from 'expo-router';
import { storage } from './storage';

// Configure deep linking URL scheme
const linking = {
  prefixes: ['cyberx://', 'https://cyberx.app'],
  config: {
    screens: {
      article: {
        path: '/article',
        parse: {
          url: (url: string) => decodeURIComponent(url),
        },
      },
    },
  },
};

class DeepLinkingService {
  // Initialize deep linking
  static initialize() {
    // Handle initial URL if app was opened from notification
    Linking.getInitialURL().then((url) => {
      if (url) {
        this.handleDeepLink(url);
      }
    });

    // Handle URLs when app is already open
    Linking.addEventListener('url', (event) => {
      this.handleDeepLink(event.url);
    });
  }

  // Handle deep link URLs
  static async handleDeepLink(url: string) {
    try {
      console.log('📱 Handling deep link:', url);
      
      const parsed = Linking.parse(url);
      const { path, queryParams } = parsed;
      
      if (path?.includes('article') && queryParams?.url) {
        // Navigate to article view with the URL
        await this.openArticle(queryParams.url as string);
      }
    } catch (error) {
      console.error('Error handling deep link:', error);
    }
  }

  // Open article from notification
  static async openArticle(articleUrl: string) {
    try {
      // Check if there's additional notification data
      const notificationData = await storage.getItem('notification_article');
      
      if (notificationData) {
        const data = JSON.parse(notificationData);
        
        // Clear the notification data
        await storage.removeItem('notification_article');
        
        // Navigate to article view
        router.push({
          pathname: '/article-view/[id]',
          params: { 
            id: encodeURIComponent(articleUrl),
            fromNotification: 'true',
            source: data.source || 'Unknown',
            category: data.category || 'News'
          }
        });
        
        console.log('📖 Opened article from notification:', data.source);
      } else {
        // Standard article opening
        router.push({
          pathname: '/article-view/[id]',
          params: { 
            id: encodeURIComponent(articleUrl),
            fromNotification: 'false'
          }
        });
      }
    } catch (error) {
      console.error('Error opening article from deep link:', error);
      
      // Fallback: just navigate to the main app
      router.push('/feed');
    }
  }

  // Create deep link URL
  static createArticleLink(articleUrl: string): string {
    return `cyberx://article?url=${encodeURIComponent(articleUrl)}`;
  }
}

export { DeepLinkingService, linking };
