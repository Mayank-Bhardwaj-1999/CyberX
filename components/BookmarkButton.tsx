import React from 'react';
import { TouchableOpacity } from 'react-native';
import { useTheme } from '../store/ThemeContext';
import { useBookmarks } from '../hooks/useBookmarks';
import { Colors } from '../constants/Colors';
import { MaterialIcons } from '@expo/vector-icons';
import type { Article } from '../types/news';

interface BookmarkButtonProps {
  article: Article;
}

export function BookmarkButton({ article }: BookmarkButtonProps) {
  const { theme } = useTheme();
  const colors = Colors[theme === 'auto' ? 'light' : theme];
  const { isBookmarked, addBookmark, removeBookmark } = useBookmarks();

  const bookmarked = isBookmarked(article.url);

  const handleToggleBookmark = () => {
    if (bookmarked) {
      removeBookmark(article.url);
    } else {
      addBookmark(article);
    }
  };

  return (
    <TouchableOpacity 
      onPress={handleToggleBookmark} 
      style={{ 
        padding: 8, 
        borderRadius: 20,
        backgroundColor: bookmarked ? colors.primaryContainer : colors.surfaceVariant
      }}
    >
      <MaterialIcons
        name={bookmarked ? 'bookmark' : 'bookmark-border'}
        size={20}
        color={bookmarked ? colors.primary : colors.textSecondary}
      />
    </TouchableOpacity>
  );
}
