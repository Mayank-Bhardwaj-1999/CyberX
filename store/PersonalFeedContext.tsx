import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { Article } from '../types/news';
import { fetchPersonalizedArticles } from '../services/personalFeedService';
import { useNotifications } from './NotificationContext';

export interface FeedTopic {
  id: string;          // unique slug
  label: string;       // display label
  query: string;       // actual search query string
  type: 'custom' | 'sector';
}

interface PersonalFeedContextValue {
  topics: FeedTopic[];
  articles: Article[];
  isLoading: boolean;
  error: string | null;
  addTopic: (label: string, queryOverride?: string, type?: 'custom' | 'sector') => Promise<void>;
  removeTopic: (id: string) => Promise<void>;
  refresh: () => Promise<void>;
  lastUpdated: number | null;
  setTopics: (topics: FeedTopic[]) => Promise<void>;
}

const PersonalFeedContext = createContext<PersonalFeedContextValue | undefined>(undefined);

const TOPICS_KEY = 'personal_feed_topics_v2';
const CACHE_KEY = 'personal_feed_cache_v1';

interface CachedFeed { timestamp: number; articles: Article[]; }

export const PersonalFeedProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { addNotification } = useNotifications();
  const [topics, setTopicsState] = useState<FeedTopic[]>([]);
  const [articles, setArticles] = useState<Article[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<number | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const storedTopics = await AsyncStorage.getItem(TOPICS_KEY);
        if (storedTopics) {
          try {
            const parsed = JSON.parse(storedTopics);
            if (Array.isArray(parsed) && parsed.length && typeof parsed[0] === 'string') {
              // migrate old string[] format
              const migrated: FeedTopic[] = parsed.map((t: string) => ({
                id: slugify(t),
                label: t,
                query: t,
                type: 'custom'
              }));
              setTopicsState(migrated);
            } else {
              setTopicsState(parsed);
            }
          } catch {
            // ignore
          }
        }
        const cached = await AsyncStorage.getItem(CACHE_KEY);
        if (cached) {
          const parsed: CachedFeed = JSON.parse(cached);
          setArticles(parsed.articles);
          setLastUpdated(parsed.timestamp);
        }
      } catch (e) {
        // ignore
      }
    })();
  }, []);

  const persistTopics = async (next: FeedTopic[]) => {
    setTopicsState(next);
    await AsyncStorage.setItem(TOPICS_KEY, JSON.stringify(next));
  };

  const setTopics = async (next: FeedTopic[]) => {
    await persistTopics(next);
    await refresh(next, true);
  };

  const slugify = (text: string) => text.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'');

  const addTopic = useCallback(async (label: string, queryOverride?: string, type: 'custom' | 'sector' = 'custom') => {
    const trimmed = label.trim();
    if (!trimmed) return;
    const id = slugify(trimmed + (type==='sector'?'-'+type:''));
    if (topics.some(t => t.id === id)) return;
    const topic: FeedTopic = { id, label: trimmed, query: queryOverride || trimmed, type };
    const next = [...topics, topic];
    await setTopics(next);
  }, [topics]);

  const removeTopic = useCallback(async (id: string) => {
    const next = topics.filter(t => t.id !== id);
    await setTopics(next);
  }, [topics]);

  const refresh = useCallback(async (useTopics?: FeedTopic[], force = false) => {
    const activeTopics = (useTopics || topics).filter(Boolean);
    if (activeTopics.length === 0) {
      setArticles([]);
      setLastUpdated(Date.now());
      return;
    }
    if (!force && lastUpdated && Date.now() - lastUpdated < 10 * 60 * 1000) {
      return; // throttle refresh
    }
    try {
      setIsLoading(true);
      setError(null);
      const previousUrls = new Set(articles.map(a=>a.url));
      const fetched = await fetchPersonalizedArticles(activeTopics.map(t=>t.query), 20);
      setArticles(fetched);
      const timestamp = Date.now();
      setLastUpdated(timestamp);
      await AsyncStorage.setItem(CACHE_KEY, JSON.stringify({ timestamp, articles: fetched } as CachedFeed));
      // Create notifications for new articles (limit 3) within last 15 minutes
      const fifteenMinAgo = Date.now() - 15*60*1000;
      let created = 0;
      for (const art of fetched) {
        if (created >= 3) break;
        if (!previousUrls.has(art.url) && new Date(art.publishedAt).getTime() >= fifteenMinAgo) {
          addNotification({
            title: art.title,
            source: 'Feed',
            timestamp: Date.now(),
            articleUrl: art.url,
            kind: 'feed'
          } as any);
          created++;
        }
      }
    } catch (e: any) {
      setError(e.message || 'Failed loading personalized feed');
    } finally {
      setIsLoading(false);
    }
  }, [topics, lastUpdated]);

  useEffect(() => {
  if (topics.length) refresh(topics, false);
  }, [topics]);

  return (
  <PersonalFeedContext.Provider value={{ topics, articles, isLoading, error, addTopic, removeTopic, refresh: () => refresh(undefined, true), lastUpdated, setTopics }}>
      {children}
    </PersonalFeedContext.Provider>
  );
};

export const usePersonalFeed = () => {
  const ctx = useContext(PersonalFeedContext);
  if (!ctx) throw new Error('usePersonalFeed must be used within PersonalFeedProvider');
  return ctx;
};
