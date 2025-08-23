import { useEffect, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { Article } from '../types/news';

const OFFLINE_NEWS_KEY = 'offline_news';

export function useOfflineNews() {
  const [offlineNews, setOfflineNews] = useState<Article[]>([]);

  useEffect(() => {
    loadOfflineNews();
  }, []);

  const loadOfflineNews = async () => {
    try {
      const stored = await AsyncStorage.getItem(OFFLINE_NEWS_KEY);
      if (stored) {
        setOfflineNews(JSON.parse(stored));
      }
    } catch (error) {
      console.error('Error loading offline news:', error);
    }
  };

  const saveForOffline = async (articles: Article[]) => {
    try {
      await AsyncStorage.setItem(OFFLINE_NEWS_KEY, JSON.stringify(articles));
      setOfflineNews(articles);
    } catch (error) {
      console.error('Error saving offline news:', error);
    }
  };

  const clearOfflineNews = async () => {
    try {
      await AsyncStorage.removeItem(OFFLINE_NEWS_KEY);
      setOfflineNews([]);
    } catch (error) {
      console.error('Error clearing offline news:', error);
    }
  };

  return {
    offlineNews,
    saveForOffline,
    clearOfflineNews,
  };
}
