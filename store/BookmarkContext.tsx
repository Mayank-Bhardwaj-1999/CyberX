import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { storage } from '../services/storage';
import type { Article } from '../types/news';

interface BookmarkContextType {
  bookmarks: Article[];
  addBookmark: (article: Article) => void;
  removeBookmark: (url: string) => void;
  isBookmarked: (url: string) => boolean;
  getBookmark: (url: string) => Article | undefined;
}

export const BookmarkContext = createContext<BookmarkContextType | undefined>(undefined);

const BOOKMARKS_KEY = 'bookmarks';

export function BookmarkProvider({ children }: { children: ReactNode }) {
  const [bookmarks, setBookmarks] = useState<Article[]>([]);

  useEffect(() => {
    loadBookmarks();
  }, []);

  const loadBookmarks = async () => {
    try {
      const stored = await storage.getItem(BOOKMARKS_KEY);
      if (stored) {
        setBookmarks(JSON.parse(stored));
      }
    } catch (error) {
      console.error('Error loading bookmarks:', error);
    }
  };

  const saveBookmarks = async (newBookmarks: Article[]) => {
    try {
      await storage.setItem(BOOKMARKS_KEY, JSON.stringify(newBookmarks));
      setBookmarks(newBookmarks);
    } catch (error) {
      console.error('Error saving bookmarks:', error);
    }
  };

  const addBookmark = (article: Article) => {
    const newBookmarks = [...bookmarks.filter(b => b.url !== article.url), article];
    saveBookmarks(newBookmarks);
  };

  const removeBookmark = (url: string) => {
    const newBookmarks = bookmarks.filter(b => b.url !== url);
    saveBookmarks(newBookmarks);
  };

  const isBookmarked = (url: string) => {
    return bookmarks.some(b => b.url === url);
  };

  const getBookmark = (url: string) => {
    return bookmarks.find(b => b.url === url);
  };

  return (
    <BookmarkContext.Provider
      value={{
        bookmarks,
        addBookmark,
        removeBookmark,
        isBookmarked,
        getBookmark,
      }}
    >
      {children}
    </BookmarkContext.Provider>
  );
}
