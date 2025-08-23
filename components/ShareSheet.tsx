import React from 'react';
import { TouchableOpacity, Share } from 'react-native';
import { useTheme } from '../store/ThemeContext';
import { Colors } from '../constants/Colors';
import { Feather } from '@expo/vector-icons';
import type { Article } from '../types/news';

interface ShareSheetProps {
  article: Article;
}

export function ShareSheet({ article }: ShareSheetProps) {
  const { theme } = useTheme();
  const colors = Colors[theme === 'auto' ? 'light' : theme];

  const handleShare = async () => {
    try {
      await Share.share({
        message: `${article.title}\n\nRead more: ${article.url}`,
        url: article.url,
        title: article.title,
      });
    } catch (error) {
      console.error('Error sharing article:', error);
    }
  };

  return (
    <TouchableOpacity onPress={handleShare} style={{ padding: 8 }}>
      <Feather name="share" size={20} color={colors.textSecondary} />
    </TouchableOpacity>
  );
}
