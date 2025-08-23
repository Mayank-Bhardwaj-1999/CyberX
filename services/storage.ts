import AsyncStorage from '@react-native-async-storage/async-storage';

// Storage keys
const STORAGE_KEYS = {
  BOOKMARKS: 'bookmarks',
  THEME: 'theme',
  NOTIFICATIONS: 'notifications',
  OFFLINE_ARTICLES: 'offline_articles',
  OFFLINE_ARTICLES_META: 'offline_articles_meta',
  EXTRACT_CACHE_INDEX: 'extract_cache_index',
  READER_MODE: 'reader_mode_pref',
  READING_SESSIONS: 'reading_sessions',
} as const;

class StorageService {
  // Generic methods
  async setItem(key: string, value: any): Promise<void> {
    try {
      const jsonValue = JSON.stringify(value);
      await AsyncStorage.setItem(key, jsonValue);
    } catch (error) {
      console.error('Error saving to storage:', error);
    }
  }

  async getItem(key: string): Promise<any> {
    try {
      const jsonValue = await AsyncStorage.getItem(key);
      return jsonValue != null ? JSON.parse(jsonValue) : null;
    } catch (error) {
      console.error('Error reading from storage:', error);
      return null;
    }
  }

  async removeItem(key: string): Promise<void> {
    try {
      await AsyncStorage.removeItem(key);
    } catch (error) {
      console.error('Error removing from storage:', error);
    }
  }

  async clear(): Promise<void> {
    try {
      await AsyncStorage.clear();
    } catch (error) {
      console.error('Error clearing storage:', error);
    }
  }

  // ===== Readable extraction cache (simple LRU with TTL) =====
  async cacheExtractedArticle(url: string, payload: any, ttlMinutes = 180): Promise<void> {
    try {
      const key = `extract_${url}`;
      const index = await this.getItem(STORAGE_KEYS.EXTRACT_CACHE_INDEX) || {};
      index[url] = { savedAt: Date.now(), ttl: ttlMinutes * 60 * 1000 };
      await this.setItem(STORAGE_KEYS.EXTRACT_CACHE_INDEX, index);
      await this.setItem(key, { ...payload, cachedAt: Date.now(), ttl: ttlMinutes * 60 * 1000 });
      // Prune if more than 60 cached
      const urls = Object.keys(index);
      if (urls.length > 60) {
        urls.sort((a,b) => (index[a].savedAt - index[b].savedAt));
        const toRemove = urls.slice(0, urls.length - 60);
        for (const u of toRemove) {
          await this.removeItem(`extract_${u}`);
          delete index[u];
        }
        await this.setItem(STORAGE_KEYS.EXTRACT_CACHE_INDEX, index);
      }
    } catch (e) {
      console.warn('cacheExtractedArticle failed', e);
    }
  }

  async getCachedExtractedArticle(url: string): Promise<any | null> {
    try {
      const key = `extract_${url}`;
      const payload = await this.getItem(key);
      if (!payload) return null;
      const expired = Date.now() - payload.cachedAt > payload.ttl;
      if (expired) {
        await this.removeItem(key);
        return null;
      }
      return payload;
    } catch (e) {
      return null;
    }
  }

  // Bookmark methods
  async getBookmarks(): Promise<string[]> {
    return await this.getItem(STORAGE_KEYS.BOOKMARKS) || [];
  }

  async addBookmark(articleUrl: string): Promise<void> {
    const bookmarks = await this.getBookmarks();
    if (!bookmarks.includes(articleUrl)) {
      bookmarks.push(articleUrl);
      await this.setItem(STORAGE_KEYS.BOOKMARKS, bookmarks);
    }
  }

  async removeBookmark(articleUrl: string): Promise<void> {
    const bookmarks = await this.getBookmarks();
    const filteredBookmarks = bookmarks.filter(url => url !== articleUrl);
    await this.setItem(STORAGE_KEYS.BOOKMARKS, filteredBookmarks);
  }

  async isBookmarked(articleUrl: string): Promise<boolean> {
    const bookmarks = await this.getBookmarks();
    return bookmarks.includes(articleUrl);
  }

  // Theme methods
  async getTheme(): Promise<string | null> {
    return await this.getItem(STORAGE_KEYS.THEME);
  }

  async setTheme(theme: string): Promise<void> {
    await this.setItem(STORAGE_KEYS.THEME, theme);
  }

  // Notification methods
  async getNotifications(): Promise<any[]> {
    return await this.getItem(STORAGE_KEYS.NOTIFICATIONS) || [];
  }

  async setNotifications(notifications: any[]): Promise<void> {
    await this.setItem(STORAGE_KEYS.NOTIFICATIONS, notifications);
  }

  // Offline articles methods
  async saveArticleForOffline(article: any): Promise<void> {
    try {
      const articleKey = `article_${article.url}`;
      
      // Save article content
      await this.setItem(articleKey, {
        ...article,
        savedForOffline: true,
        savedAt: new Date().toISOString(),
      });

      // Update metadata
      const metadata = await this.getOfflineArticlesMeta();
      metadata[article.url] = {
        title: article.title,
        source: article.source?.name,
        publishedAt: article.publishedAt,
        savedAt: new Date().toISOString(),
      };
      
      await this.setItem(STORAGE_KEYS.OFFLINE_ARTICLES_META, metadata);
    } catch (error) {
      console.error('Error saving article for offline:', error);
    }
  }

  async getOfflineArticles(): Promise<any[]> {
    try {
      const metadata = await this.getOfflineArticlesMeta();
      const articles = [];
      
  for (const [url] of Object.entries(metadata)) {
        const articleKey = `article_${url}`;
        const article = await this.getItem(articleKey);
        if (article) {
          articles.push(article);
        }
      }
      
      return articles.sort((a, b) => 
        new Date(b.savedAt).getTime() - new Date(a.savedAt).getTime()
      );
    } catch (error) {
      console.error('Error getting offline articles:', error);
      return [];
    }
  }

  async getOfflineArticlesMeta(): Promise<Record<string, any>> {
    return await this.getItem(STORAGE_KEYS.OFFLINE_ARTICLES_META) || {};
  }

  async removeOfflineArticle(articleUrl: string): Promise<void> {
    try {
      const articleKey = `article_${articleUrl}`;
      await this.removeItem(articleKey);
      
      const metadata = await this.getOfflineArticlesMeta();
      delete metadata[articleUrl];
      await this.setItem(STORAGE_KEYS.OFFLINE_ARTICLES_META, metadata);
    } catch (error) {
      console.error('Error removing offline article:', error);
    }
  }

  async isArticleOffline(articleUrl: string): Promise<boolean> {
    const metadata = await this.getOfflineArticlesMeta();
    return articleUrl in metadata;
  }

  async clearOfflineArticles(): Promise<void> {
    try {
      const metadata = await this.getOfflineArticlesMeta();
      
      // Remove all article data
      for (const url of Object.keys(metadata)) {
        const articleKey = `article_${url}`;
        await this.removeItem(articleKey);
      }
      
      // Clear metadata
      await this.removeItem(STORAGE_KEYS.OFFLINE_ARTICLES_META);
    } catch (error) {
      console.error('Error clearing offline articles:', error);
    }
  }

  async getOfflineStorageSize(): Promise<number> {
    try {
      const metadata = await this.getOfflineArticlesMeta();
      return Object.keys(metadata).length;
    } catch (error) {
      console.error('Error getting offline storage size:', error);
      return 0;
    }
  }

  // Reader mode preference
  async getReaderMode(): Promise<string | null> {
    return await this.getItem(STORAGE_KEYS.READER_MODE);
  }
  async setReaderMode(mode: string): Promise<void> {
    await this.setItem(STORAGE_KEYS.READER_MODE, mode);
  }

  // Reading session tracking (append, cap 100 entries)
  async addReadingSession(articleUrl: string, mode: string, durationMs: number): Promise<void> {
    try {
      const sessions = await this.getItem(STORAGE_KEYS.READING_SESSIONS) || [];
      sessions.push({ url: articleUrl, mode, durationMs, ts: Date.now() });
      if (sessions.length > 100) sessions.splice(0, sessions.length - 100);
      await this.setItem(STORAGE_KEYS.READING_SESSIONS, sessions);
    } catch (e) {
      console.warn('addReadingSession failed', e);
    }
  }
  async getReadingSessions(): Promise<any[]> { return await this.getItem(STORAGE_KEYS.READING_SESSIONS) || []; }
}

export const storage = new StorageService();
