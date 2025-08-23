import { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import { Feather } from '@expo/vector-icons';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';
import { ModernArticleViewScreen } from '../../components/ui/ModernArticleViewScreen';
import type { Article } from '../../types/news';

export default function ArticleViewScreenPage() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { theme } = useTheme();
  const colors = Colors[theme === 'auto' ? 'light' : theme];
  const [article, setArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      // Decode the article ID and fetch the article
      const decodedId = decodeURIComponent(id);
      fetchArticle(decodedId);
    }
  }, [id]);

  const fetchArticle = async (articleId: string) => {
    try {
      // Direct API call to avoid import issues
      const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'https://cyberx.icu';
      const response = await fetch(`${API_BASE_URL}/api/article/${encodeURIComponent(articleId)}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.status === 'success' && data.article) {
        setArticle(data.article);
      } else {
        throw new Error(data.message || 'Article not found');
      }
    } catch (error) {
      setArticle(null);
    } finally {
      setLoading(false);
    }
  };

  // Show loading state while fetching
  if (loading) {
    return (
      <View style={[styles.container, styles.centered, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>Loading article...</Text>
      </View>
    );
  }

  // Show error state if article not found after loading
  if (!article) {
    return (
      <View style={[styles.container, styles.centered, { backgroundColor: colors.background }]}>
        <Feather name="alert-circle" size={48} color={colors.textSecondary} />
        <Text style={[styles.errorText, { color: colors.textSecondary }]}>Article not found</Text>
        <TouchableOpacity
          style={[styles.button, { backgroundColor: colors.primary }]}
          onPress={() => router.back()}
        >
          <Text style={[styles.buttonText, { color: colors.background }]}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <ModernArticleViewScreen article={article} onBack={() => router.back()} />
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.1)',
  },
  headerButton: {
    padding: 8,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  scrollContent: {
    flex: 1,
  },
  articleImage: {
    width: '100%',
    height: 250,
    resizeMode: 'cover',
  },
  articleContent: {
    padding: 16,
  },
  metadata: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  source: {
    ...Typography.caption,
    fontSize: 14,
    fontWeight: '700',
    textTransform: 'uppercase',
  },
  date: {
    ...Typography.caption,
    fontSize: 12,
  },
  title: {
    ...Typography.title,
    fontSize: 24,
    fontWeight: '800',
    lineHeight: 32,
    marginBottom: 8,
  },
  author: {
    ...Typography.caption,
    fontSize: 14,
    fontStyle: 'italic',
    marginBottom: 20,
  },
  summaryContainer: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
  },
  summaryLabel: {
    ...Typography.caption,
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    marginBottom: 8,
  },
  summary: {
    ...Typography.body,
    fontSize: 16,
    lineHeight: 24,
    fontWeight: '500',
  },
  content: {
    ...Typography.body,
    fontSize: 16,
    lineHeight: 28,
    marginBottom: 24,
  },
  readOriginalButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    marginTop: 20,
    gap: 8,
  },
  readOriginalText: {
    ...Typography.body,
    fontSize: 16,
    fontWeight: '700',
  },
  loadingText: {
    ...Typography.body,
    fontSize: 16,
    marginTop: 16,
  },
  errorText: {
    ...Typography.body,
    fontSize: 16,
    marginTop: 16,
    marginBottom: 24,
  },
  button: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  buttonText: {
    ...Typography.body,
    fontSize: 16,
    fontWeight: '600',
  },
});