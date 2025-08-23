import { useContext } from 'react';
import { BookmarkContext } from '../store/BookmarkContext';

export function useBookmarks() {
  const context = useContext(BookmarkContext);
  if (!context) {
    throw new Error('useBookmarks must be used within a BookmarkProvider');
  }
  return context;
}
