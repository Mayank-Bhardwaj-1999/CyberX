import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { Article } from '../types/news';

interface ReactionState {
  liked: boolean;
  disliked: boolean;
  likeCount: number; // heuristic local count
  updatedAt: number;
}

interface LikeDislikeContextType {
  reactions: Record<string, ReactionState>;
  toggleLike: (article: Article) => void;
  toggleDislike: (article: Article) => void;
  getReaction: (id: string) => ReactionState | undefined;
}

const STORAGE_KEY = 'article_reactions_v1';
const LikeDislikeContext = createContext<LikeDislikeContextType | undefined>(undefined);

export function LikeDislikeProvider({ children }: { children: ReactNode }) {
  const [reactions, setReactions] = useState<Record<string, ReactionState>>({});

  useEffect(() => {
    (async () => {
      try {
        const stored = await AsyncStorage.getItem(STORAGE_KEY);
        if (stored) setReactions(JSON.parse(stored));
      } catch (e) {
        console.warn('Failed loading reactions', e);
      }
    })();
  }, []);

  const persist = useCallback(async (next: Record<string, ReactionState>) => {
    setReactions(next);
    try { await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next)); } catch {}
  }, []);

  const articleKey = (article: Article) => article.url; // stable unique key

  const toggleLike = (article: Article) => {
    const key = articleKey(article);
    const current = reactions[key];
    let nextState: ReactionState;
    if (current?.liked) {
      nextState = { liked: false, disliked: false, likeCount: Math.max(0, (current.likeCount || 1) - 1), updatedAt: Date.now() };
    } else {
      const base = current?.likeCount ?? Math.floor(Math.random() * 40) + 10;
      const adjust = current?.disliked ? 2 : 1;
      nextState = { liked: true, disliked: false, likeCount: base + adjust, updatedAt: Date.now() };
    }
    persist({ ...reactions, [key]: nextState });
  };

  const toggleDislike = (article: Article) => {
    const key = articleKey(article);
    const current = reactions[key];
    let nextState: ReactionState;
    if (current?.disliked) {
      const restored = (current.likeCount || 0) + 1;
      nextState = { liked: false, disliked: false, likeCount: restored, updatedAt: Date.now() };
    } else {
      const base = current?.likeCount ?? Math.floor(Math.random() * 40) + 10;
      const adjust = current?.liked ? 2 : 0;
      nextState = { liked: false, disliked: true, likeCount: Math.max(0, base - 1 - adjust), updatedAt: Date.now() };
    }
    persist({ ...reactions, [key]: nextState });
  };

  const getReaction = (id: string) => reactions[id];

  return (
    <LikeDislikeContext.Provider value={{ reactions, toggleLike, toggleDislike, getReaction }}>
      {children}
    </LikeDislikeContext.Provider>
  );
}

export function useReactions() {
  const ctx = useContext(LikeDislikeContext);
  if (!ctx) throw new Error('useReactions must be used within LikeDislikeProvider');
  return ctx;
}
