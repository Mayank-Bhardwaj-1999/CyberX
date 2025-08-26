import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  StatusBar,
  RefreshControl,
  ScrollView,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useTheme } from '../../store/ThemeContext';
import { usePersonalFeed } from '../../store/PersonalFeedContext';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';
import { Layout } from '../../constants/Layout';
import { ProfessionalHeader } from '../../components/ProfessionalHeader';
import { ModernNewsCard } from '../../components/ui/ModernNewsCard';
import { EnhancedSearchBar } from '../../components/EnhancedSearchBar';
import { MaterialCard } from '../../components/ui/MaterialComponents';
import { NewsCardSkeleton } from '../../components/ui/LoadingSkeleton';
import { EmptyState } from '../../components/ui/EmptyState';
import { useNews } from '../../hooks/useNews';
import { useThreatMonitoring } from '../../services/threatMonitoring';
import { getThreatLevel } from '../../utils/threatAnalysis';
import type { Article } from '../../types/news';

export default function NewsScreen() {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const [selectedCategory, setSelectedCategory] = useState('all');
  // viewMode: 'default' = rich cards, 'compact' = list view (user toggle)
  const [viewMode, setViewMode] = useState<'default' | 'compact'>('default');
  const [refreshing, setRefreshing] = useState(false);
  // const router = useRouter(); // Router available if needed

  const { articles, isLoading, error, refetch, loadMore, loadingMore, hasMore } = useNews();
  const { articles: feedArticles } = usePersonalFeed();
  const [visibleCount, setVisibleCount] = useState(20);
  const listRef = useState<FlatList | null>(null)[0];
  const [showScrollTop, setShowScrollTop] = useState(false);
  const [showFloatingLoadMore, setShowFloatingLoadMore] = useState(false);
  const insets = useSafeAreaInsets();
  const { processArticles } = useThreatMonitoring();

  // Categories with modern threat-focused design
  const categories = [
    { id: 'all', name: 'All News', icon: 'globe', color: colors.primary },
    { id: 'breaking', name: 'Breaking', icon: 'alert-circle', color: colors.critical },
    { id: 'malware', name: 'Malware', icon: 'alert-triangle', color: colors.threat },
    { id: 'breach', name: 'Data Breach', icon: 'database', color: colors.critical },
    { id: 'vulnerability', name: 'CVE', icon: 'shield-off', color: colors.vulnerability },
    { id: 'phishing', name: 'Phishing', icon: 'mail', color: colors.malware },
    { id: 'ransomware', name: 'Ransomware', icon: 'lock', color: colors.security },
  ];

  // Removed aggressive auto-refresh to improve UX and prevent lag
  // Users can manually refresh by pulling down
  
  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  }, [refetch]);

  const handleCategoryPress = useCallback((categoryId: string) => {
    setSelectedCategory(categoryId);
  }, []);

  const filteredArticles = selectedCategory === 'all' 
    ? articles 
    : articles.filter(article => {
        const text = `${article.title} ${article.description} ${article.content}`.toLowerCase();
        const keywords = {
          breaking: ['breaking', 'urgent', 'alert', 'critical'],
          malware: ['malware', 'virus', 'trojan', 'worm', 'spyware'],
          phishing: ['phishing', 'spear phishing', 'email scam', 'social engineering'],
          breach: ['data breach', 'data leak', 'stolen data', 'hack'],
          ransomware: ['ransomware', 'crypto locker', 'ransom demand'],
          vulnerability: ['vulnerability', 'cve-', 'zero-day', 'exploit', 'patch'],
          critical: ['critical', 'breach', 'ransomware', 'zero-day', 'compromised', 'emergency'],
        };
        
        const categoryKeywords = keywords[selectedCategory as keyof typeof keywords] || [];
        return categoryKeywords.some(keyword => text.includes(keyword));
      });

  const renderCategoryChip = ({ item }: { item: typeof categories[0] }) => {
    const isSelected = selectedCategory === item.id;
    return (
      <TouchableOpacity
        style={[
          styles.categoryChip,
          {
            backgroundColor: isSelected ? item.color : colors.surfaceContainer,
            borderColor: isSelected ? item.color : colors.outline,
          }
        ]}
        onPress={() => handleCategoryPress(item.id)}
        activeOpacity={0.8}
      >
        <Feather 
          name={item.icon as any} 
          size={16} 
          color={isSelected ? colors.onPrimary : colors.textSecondary} 
        />
        <Text style={[
          Typography.labelMedium,
          { 
            color: isSelected ? colors.onPrimary : colors.textSecondary,
            marginLeft: 6,
          }
        ]}>
          {item.name}
        </Text>
        {item.id === 'breaking' && (
          <View style={[styles.liveBadge, { backgroundColor: colors.critical }]}>
            <Text style={[Typography.labelSmall, { color: colors.onPrimary, fontSize: 8 }]}>
              LIVE
            </Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  const renderArticleItem = ({ item }: { item: Article }) => {
    // Use ModernNewsCard to honor list toggle; map 'compact' to ModernNewsCard list view
    if (viewMode === 'compact') {
      return (
        <ModernNewsCard
          article={item}
          viewMode="list"
          onPress={() => router.push(`/article-view/${encodeURIComponent(item.url)}`)}
        />
      );
    }
    return (
      <ModernNewsCard
        article={item}
        viewMode="default"
        onPress={() => router.push(`/article-view/${encodeURIComponent(item.url)}`)}
      />
    );
  };

  // Process incoming articles into threat monitoring service to keep statistics fresh
  useEffect(() => {
    if (articles && articles.length) {
      processArticles(articles);
    }
  }, [articles, processArticles]);

  const renderHeader = () => (
    <View style={styles.headerContainer}>
      <ProfessionalHeader
        title="CyberX Intelligence"
        subtitle="Real-time cybersecurity threats"
        showGradient={true}
        elevation={3}
      />
      
      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <EnhancedSearchBar placeholder="Search cybersecurity intelligence..." />
      </View>

      {/* Stats Cards (display-only for better performance) */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.statsContainer}>
        {/* Total Alerts - shows total news count from API */}
        <MaterialCard variant="elevated" style={[styles.statCard, { backgroundColor: colors.primaryContainer }]}>
          <View style={styles.statContent}>
            <Feather name="shield" size={24} color={colors.primary} />
            <Text style={[Typography.headlineSmall, { color: colors.onPrimaryContainer }]}>
              {articles?.length ?? 0}
            </Text>
            <Text style={[Typography.bodyMedium, { color: colors.onPrimaryContainer, opacity: 0.8 }]}>
              Total News
            </Text>
          </View>
        </MaterialCard>

        {/* Critical Threats - shows only critical threats count */}
        <TouchableOpacity
          onPress={() => setSelectedCategory('critical')}
          activeOpacity={0.7}
        >
          <MaterialCard variant="elevated" style={[styles.statCard, { backgroundColor: colors.errorContainer }]}>
            <View style={styles.statContent}>
              <Feather name="alert-triangle" size={24} color={colors.error} />
              <Text style={[Typography.headlineSmall, { color: colors.onErrorContainer }]}>
                {articles.filter(a => getThreatLevel(a) === 'critical').length}
              </Text>
              <Text style={[Typography.bodyMedium, { color: colors.onErrorContainer, opacity: 0.8 }]}>
                Critical Threats
              </Text>
            </View>
          </MaterialCard>
        </TouchableOpacity>

        {/* Personal Feed - shows articles matching user's feed topics */}
        <MaterialCard variant="elevated" style={[styles.statCard, { backgroundColor: colors.secondaryContainer }]}>
          <View style={styles.statContent}>
            <Feather name="rss" size={24} color={colors.secondary} />
            <Text style={[Typography.headlineSmall, { color: colors.onSecondaryContainer }]}>
              {feedArticles?.length ?? 0}
            </Text>
            <Text style={[Typography.bodyMedium, { color: colors.onSecondaryContainer, opacity: 0.8 }]}>
              My Feed
            </Text>
          </View>
        </MaterialCard>
      </ScrollView>

      {/* Category Filters */}
      <View style={styles.categorySection}>
        <View style={styles.categoryHeader}>
          <Text style={[Typography.titleMedium, { color: colors.text }]}>
            Threat Categories
          </Text>
          <View style={styles.viewModeToggle}>
            <TouchableOpacity
              style={[
                styles.viewModeButton,
                { backgroundColor: viewMode === 'default' ? colors.primary : colors.surfaceContainer }
              ]}
              onPress={() => setViewMode('default')}
            >
              <Feather 
                name="grid" 
                size={16} 
                color={viewMode === 'default' ? colors.onPrimary : colors.textSecondary} 
              />
            </TouchableOpacity>
            <TouchableOpacity
              style={[
                styles.viewModeButton,
                { backgroundColor: viewMode === 'compact' ? colors.primary : colors.surfaceContainer }
              ]}
              onPress={() => setViewMode('compact')}
            >
              <Feather 
                name="list" 
                size={16} 
                color={viewMode === 'compact' ? colors.onPrimary : colors.textSecondary} 
              />
            </TouchableOpacity>
          </View>
        </View>

        <FlatList
          data={categories}
          renderItem={renderCategoryChip}
          keyExtractor={(item) => item.id}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.categoriesContainer}
          ItemSeparatorComponent={() => <View style={{ width: 8 }} />}
        />
      </View>
    </View>
  );

  if (error) {
    return (
      <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
        <StatusBar barStyle={resolvedTheme === 'dark' ? 'light-content' : 'dark-content'} />
        <EmptyState
          title="Connection Error"
          subtitle="Failed to load cybersecurity intelligence. Check your connection and try again."
          action={{
            label: "Retry",
            onPress: () => refetch()
          }}
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle={resolvedTheme === 'dark' ? 'light-content' : 'dark-content'} />
      
      <FlatList
        ref={(ref) => { /* store ref */ (listRef as any) = ref; }}
        data={filteredArticles.slice(0, visibleCount)}
        renderItem={renderArticleItem}
        keyExtractor={(item, index) => `${item.url}-${index}`}
        ListHeaderComponent={renderHeader}
        ListEmptyComponent={
          isLoading ? (
            <View style={styles.skeletonContainer}>
              {[1, 2, 3, 4, 5].map(i => <NewsCardSkeleton key={i} />)}
            </View>
          ) : (
            <EmptyState
              title="No Threats Found"
              subtitle={selectedCategory === 'all' 
                ? "No cybersecurity intelligence available at the moment." 
                : "No threats found in this category."}
              action={selectedCategory !== 'all' ? {
                label: "View All News",
                onPress: () => setSelectedCategory('all')
              } : undefined}
            />
          )
        }
        refreshControl={
          <RefreshControl 
            refreshing={refreshing} 
            onRefresh={handleRefresh}
            colors={[colors.primary]}
            tintColor={colors.primary}
          />
        }
        onScroll={(e)=>{
          const { contentOffset, contentSize, layoutMeasurement } = e.nativeEvent;
          const y = contentOffset.y;
          const distanceFromBottom = contentSize.height - (y + layoutMeasurement.height);
          // Show scroll top if scrolled down a bit OR at bottom cluster
          setShowScrollTop(y > 600 || distanceFromBottom < 200);
          setShowFloatingLoadMore(
            distanceFromBottom < 320 &&
            visibleCount < filteredArticles.length
          );
        }}
        scrollEventThrottle={16}
        ListFooterComponent={
          <View style={[styles.footerContainer,{ paddingBottom:  (insets.bottom || 16) + 140 }]}>
            {loadingMore && (
              <View style={styles.loadingMore}><NewsCardSkeleton /></View>
            )}
            {visibleCount >= filteredArticles.length && !hasMore && filteredArticles.length > 0 && (
              <Text style={[styles.endMessage, { color: colors.textSecondary }]}>No more articles</Text>
            )}
          </View>
        }
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.contentContainer}
        extraData={viewMode}
      />
      {showScrollTop && (
        <TouchableOpacity
          style={[styles.scrollTopBtn,{backgroundColor: colors.primary, bottom: (insets.bottom || 16) + 92 }]}
          onPress={()=>{ (listRef as any)?.scrollToOffset({ offset:0, animated:true }); }}
          activeOpacity={0.85}
        >
          <Feather name="arrow-up" size={18} color={colors.onPrimary} />
        </TouchableOpacity>
      )}
      {showFloatingLoadMore && (
        <TouchableOpacity
          style={[styles.fabLoadMore,{ backgroundColor: colors.primaryContainer, bottom: (insets.bottom || 16) + 86, borderWidth:1, borderColor: colors.outlineVariant }]}
          onPress={()=>{
            if (loadingMore) return;
            const next = Math.min(visibleCount + 20, filteredArticles.length);
            setVisibleCount(next);
            if (next === filteredArticles.length && hasMore) {
              loadMore();
            }
          }}
          activeOpacity={0.9}
        >
          <Feather name="plus" size={18} color={colors.onPrimaryContainer} />
          <Text style={[styles.fabLoadMoreText,{ color: colors.onPrimaryContainer }]}>{loadingMore ? 'Loading...' : 'Load More'}</Text>
        </TouchableOpacity>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  contentContainer: {
    paddingBottom: Layout.spacing.xl,
  },
  headerContainer: {
    paddingBottom: Layout.spacing.md,
  },
  searchContainer: {
    marginTop: -Layout.spacing.md,
    zIndex: 10,
  },
  statsContainer: {
    paddingHorizontal: Layout.spacing.md,
    paddingVertical: Layout.spacing.md,
  },
  statCard: {
    marginRight: Layout.spacing.md,
    padding: Layout.spacing.md,
    minWidth: 120,
  },
  statContent: {
    alignItems: 'center',
  },
  categorySection: {
    paddingHorizontal: Layout.spacing.md,
    marginBottom: Layout.spacing.sm,
  },
  categoryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Layout.spacing.md,
  },
  viewModeToggle: {
    flexDirection: 'row',
    backgroundColor: 'transparent',
    borderRadius: Layout.borderRadius.md,
  },
  viewModeButton: {
    padding: Layout.spacing.sm,
    borderRadius: Layout.borderRadius.sm,
    marginLeft: 4,
  },
  categoriesContainer: {
    paddingVertical: Layout.spacing.sm,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Layout.spacing.md,
    paddingVertical: Layout.spacing.sm,
    borderRadius: Layout.borderRadius.xl,
    borderWidth: 1,
    position: 'relative',
  },
  liveBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    paddingHorizontal: 4,
    paddingVertical: 2,
    borderRadius: 8,
  },
  skeletonContainer: {
    padding: Layout.spacing.md,
  },
  loadingMore: {
    padding: Layout.spacing.md,
  },
  footerContainer: { paddingVertical: 24, alignItems: 'center', gap: 16 },
  endMessage: { ...Typography.labelSmall, fontSize: 12 },
  scrollTopBtn:{ position:'absolute', right:16, width:48, height:48, borderRadius:24, justifyContent:'center', alignItems:'center', elevation:4, shadowColor:'#000', shadowOpacity:0.2, shadowRadius:4, shadowOffset:{width:0,height:2} },
  fabLoadMore:{ position:'absolute', alignSelf:'center', flexDirection:'row', alignItems:'center', gap:8, paddingHorizontal:22, paddingVertical:14, borderRadius:28, elevation:5, shadowColor:'#000', shadowOpacity:0.25, shadowRadius:6, shadowOffset:{width:0,height:3} },
  fabLoadMoreText:{ ...Typography.labelMedium, fontWeight:'700', letterSpacing:0.5 },
});