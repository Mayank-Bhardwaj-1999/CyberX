import { Text, StyleSheet, RefreshControl, FlatList, View, ActivityIndicator, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '../../store/ThemeContext';
import { useNews } from '../../hooks/useNews';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';
import { Layout } from '../../constants/Layout';
import { NewsCard } from '../../components/NewsCard';
import type { Article } from '../../types/news';
import { useState } from 'react';
import { Feather } from '@expo/vector-icons';

export default function EnhancedNewsScreen() {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const [refreshing, setRefreshing] = useState(false);
  const { 
    articles, 
    isLoading, 
    error,
    refetch 
  } = useNews();

  const handleRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  const renderArticleItem = ({ item }: { item: Article }) => {
    return (
      <NewsCard 
        article={item}
      />
    );
  };

  if (error) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <View style={styles.errorContainer}>
          <Feather name="wifi-off" size={48} color={colors.textSecondary} />
          <Text style={[Typography.titleLarge, { color: colors.text, marginTop: 16 }]}>
            Connection Error
          </Text>
          <Text style={[Typography.bodyMedium, { color: colors.textSecondary, marginVertical: 8, textAlign: 'center' }]}>
            Failed to load enhanced news. Check your connection and try again.
          </Text>
          <TouchableOpacity
            style={[styles.retryButton, { backgroundColor: colors.primary }]}
            onPress={handleRefresh}
          >
            <Text style={[Typography.labelLarge, { color: colors.onPrimary }]}>
              Retry
            </Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <Text style={[styles.screenTitle, { color: colors.text }]}>
        Enhanced News
      </Text>
      
      <FlatList
        data={articles}
        renderItem={renderArticleItem}
        keyExtractor={(item, index) => `${item.url}-${index}`}
        refreshControl={
          <RefreshControl 
            refreshing={refreshing} 
            onRefresh={handleRefresh}
            colors={[colors.primary]}
            tintColor={colors.primary}
          />
        }
        ListEmptyComponent={
          isLoading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color={colors.primary} />
              <Text style={[Typography.bodyMedium, { color: colors.textSecondary, marginTop: 16 }]}>
                Loading enhanced news...
              </Text>
            </View>
          ) : (
            <View style={styles.emptyContainer}>
              <Feather name="file-text" size={48} color={colors.textSecondary} />
              <Text style={[Typography.titleLarge, { color: colors.text, marginTop: 16 }]}>
                No Enhanced News
              </Text>
              <Text style={[Typography.bodyMedium, { color: colors.textSecondary, marginVertical: 8, textAlign: 'center' }]}>
                No enhanced news articles available at the moment.
              </Text>
            </View>
          )
        }
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.contentContainer}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  screenTitle: {
    ...Typography.headlineLarge,
    marginHorizontal: Layout.spacing.lg,
    marginVertical: Layout.spacing.md,
  },
  contentContainer: {
    paddingBottom: Layout.spacing.xl,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: Layout.spacing.xxl,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: Layout.spacing.xxl,
    paddingHorizontal: Layout.spacing.lg,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: Layout.spacing.lg,
  },
  retryButton: {
    paddingHorizontal: Layout.spacing.lg,
    paddingVertical: Layout.spacing.md,
    borderRadius: Layout.borderRadius.md,
    marginTop: Layout.spacing.md,
  },
});
