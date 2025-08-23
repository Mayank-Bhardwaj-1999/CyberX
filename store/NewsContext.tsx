import React, { createContext, useContext, ReactNode } from 'react';
import { useNews } from '../hooks/useNews';

interface NewsContextType {
  // This will be provided by the useNews hook
}

const NewsContext = createContext<NewsContextType | undefined>(undefined);

export function NewsProvider({ children }: { children: ReactNode }) {
  // The actual news logic is handled by the useNews hook
  // This context is kept for future global news state if needed
  return <NewsContext.Provider value={{}}>{children}</NewsContext.Provider>;
}

export function useNewsContext() {
  const context = useContext(NewsContext);
  if (context === undefined) {
    throw new Error('useNewsContext must be used within a NewsProvider');
  }
  return context;
}
