import { useState, useEffect, useRef } from 'react';
import { Article, NewsResponse } from '../types/news';
import { useOfflineNews } from './useOfflineNews';

export function useNews(_initialCategory = 'cybersecurity') {
  const [articles, setArticles] = useState<Article[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const { offlineNews, saveForOffline } = useOfflineNews();
  const abortControllerRef = useRef<AbortController | null>(null);
  const lastFetchTimeRef = useRef<number>(0);
  const FETCH_DEBOUNCE_TIME = 2000; // 2 seconds debounce

  const fetchNews = async (pageNum = 1, append = false) => {
    // Debounce rapid API calls
    const now = Date.now();
    if (now - lastFetchTimeRef.current < FETCH_DEBOUNCE_TIME) {
      return;
    }
    lastFetchTimeRef.current = now;

    // Cancel previous request if still running
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();

    try {
      if (pageNum === 1) {
        setIsLoading(true);
      } else {
        setLoadingMore(true);
      }
      
      setError(null);
      
      // Direct API call to avoid import issues
      const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'https://cyberx.icu';
  const response = await fetch(`${API_BASE_URL}/api/news?page=${pageNum}&limit=25`, {
        signal: abortControllerRef.current.signal
      });
      
      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }
      
      const data = await response.json() as NewsResponse;
      
      // Check if request was aborted
      if (abortControllerRef.current.signal.aborted) {
        return;
      }
      
      const newArticles = data.articles || [];
      
      if (append) {
        setArticles(prev => [...prev, ...newArticles]);
      } else {
        setArticles(newArticles);
      }
      
      // Save first page to offline cache
      if (pageNum === 1 && newArticles.length > 0) {
        saveForOffline(newArticles);
      }
      
      // Check if there are more articles
  setHasMore(newArticles.length === 25);
      
    } catch (err) {
      // Don't handle aborted requests as errors
      if (err instanceof Error && err.name === 'AbortError') {
        return;
      }

      const errorMessage = err instanceof Error ? err.message : 'An error occurred';
      
      setError(`Network Error: ${errorMessage}`);
      
      // Only use fallback data on first load and if we don't have articles yet
      if (pageNum === 1 && articles.length === 0) {
        if (__DEV__) {
          console.warn('Using development mock data');
          setArticles(getMockCybersecurityNews());
        } else if (offlineNews.length > 0) {
          console.warn('Using offline cached news');
          setArticles(offlineNews);
        }
      }
    } finally {
      setIsLoading(false);
      setLoadingMore(false);
      abortControllerRef.current = null;
    }
  };

  useEffect(() => {
    fetchNews(1, false);
  }, []);

  const refetch = () => {
    setPage(1);
    fetchNews(1, false);
  };

  const loadMore = () => {
    if (!loadingMore && hasMore) {
      const nextPage = page + 1;
      setPage(nextPage);
      fetchNews(nextPage, true);
    }
  };

  return {
    articles,
    isLoading,
    error,
    refetch,
    loadMore,
    loadingMore,
    hasMore,
  };
}

// Mock cybersecurity news for development when backend is not running
function getMockCybersecurityNews(): Article[] {
  return [
    {
      source: { id: 'thehackernews', name: 'TheHackerNews' },
      author: 'Security Researcher',
      title: 'New Ransomware Campaign Targets Critical Infrastructure',
      description: 'Security researchers have discovered a sophisticated ransomware campaign targeting critical infrastructure systems worldwide.',
      summary: 'Security researchers have discovered a sophisticated ransomware campaign targeting critical infrastructure systems worldwide.',
      url: 'https://example.com/news1',
      urlToImage: 'https://img.icons8.com/fluent/400/000000/cyber-security.png',
      publishedAt: new Date().toISOString(),
      content: 'A new ransomware campaign has been discovered targeting critical infrastructure...'
    },
    {
      source: { id: 'bleepingcomputer', name: 'BleepingComputer' },
      author: 'Cyber Analyst',
      title: 'Zero-Day Vulnerability Found in Popular Enterprise Software',
      description: 'A critical zero-day vulnerability has been discovered in widely-used enterprise software, affecting millions of users.',
      summary: 'A critical zero-day vulnerability has been discovered in widely-used enterprise software, affecting millions of users.',
      url: 'https://example.com/news2',
      urlToImage: 'https://img.icons8.com/fluent/400/000000/virus.png',
      publishedAt: new Date(Date.now() - 3600000).toISOString(),
      content: 'Researchers have identified a critical zero-day vulnerability...'
    },
    {
      source: { id: 'the420in', name: 'The420.in' },
      author: 'Indian Security Team',
      title: 'Government Agencies Enhance Cybersecurity Protocols',
      description: 'Indian government agencies are implementing enhanced cybersecurity protocols to protect against emerging threats.',
      summary: 'Indian government agencies are implementing enhanced cybersecurity protocols to protect against emerging threats.',
      url: 'https://example.com/news3',
      urlToImage: 'https://img.icons8.com/fluent/400/000000/privacy.png',
      publishedAt: new Date(Date.now() - 7200000).toISOString(),
      content: 'Government agencies across India are strengthening their cybersecurity measures...'
    }
  ];
}