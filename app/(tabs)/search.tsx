import { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
  RefreshControl,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';
import { MaterialIcons } from '@expo/vector-icons';
import { useDebounce } from '../../hooks/useDebounce';
import type { Article } from '../../types/news';
import { SearchResultItem } from '../../components/ui/SearchResultItem';
import { GoogleNewsService } from '../../services/googleNewsService';
import { SimpleAnalyticsService } from '../../services/simpleAnalytics';

export default function SearchTabScreen() {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Article[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  const debouncedQuery = useDebounce(searchQuery, 500);

  useEffect(() => {
    // Track screen view
    SimpleAnalyticsService.trackScreenView('Search', 'SearchTabScreen');
  }, []);

  useEffect(() => {
    if (debouncedQuery) {
      handleSearch(debouncedQuery);
    } else {
      setSearchResults([]);
    }
  }, [debouncedQuery]);

  const handleRefresh = async () => {
    setRefreshing(true);
    if (searchQuery) {
      await handleSearch(searchQuery);
    }
    setRefreshing(false);
  };

  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    console.log('🔍 Searching for:', query);
    
    try {
      const results = await GoogleNewsService.searchCyberSecurityNews(query, 20);
      console.log('✅ Search results received:', results.length);
      setSearchResults(results);
      
      // Track search analytics
      SimpleAnalyticsService.trackSearch(query, results.length);
      
      // Add to recent searches
      const updatedSearches = [query, ...recentSearches.filter(s => s !== query)].slice(0, 5);
      setRecentSearches(updatedSearches);
    } catch (error) {
      console.error('❌ Search error:', error);
      setSearchResults([]);
      
      // Track search error
      SimpleAnalyticsService.trackError(`Search failed: ${error}`, 'SearchTabScreen');
    } finally {
      setIsSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
  };

  const handleSearchSubmit = () => {
    if (searchQuery.trim()) {
      handleSearch(searchQuery.trim());
    }
  };

  const handleCategoryPress = (category: string) => {
    setSearchQuery(category);
    handleSearch(category);
  };

  const clearRecentSearches = () => {
    setRecentSearches([]);
  };

  const handleRecentSearchPress = (search: string) => {
    setSearchQuery(search);
    handleSearch(search);
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.text }]}>Search</Text>
        <TouchableOpacity onPress={handleRefresh} style={[styles.refreshBtn, { backgroundColor: colors.primaryContainer }]}>
          <MaterialIcons name="refresh" size={18} color={colors.primary} />
        </TouchableOpacity>
      </View>

      {/* Search Input */}
      <View style={[styles.inputRow, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}>
        <MaterialIcons name="search" size={20} color={colors.primary} />
        <TextInput
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholder="Search cybersecurity news..."
          placeholderTextColor={colors.textSecondary}
          style={[styles.input, { color: colors.text }]}
          autoCapitalize="none"
          returnKeyType="search"
          onSubmitEditing={handleSearchSubmit}
        />
        {searchQuery ? (
          <TouchableOpacity onPress={clearSearch}>
            <MaterialIcons name="close" size={20} color={colors.textSecondary} />
          </TouchableOpacity>
        ) : null}
      </View>

      {/* Quick Search Categories */}
      <View style={styles.categoriesContainer}>
        <View style={styles.categoriesWrap}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.categoriesScroll}>
            {[
              'Data Breach', 'Ransomware', 'Zero-Day', 'Malware', 'Phishing', 
              'APT', 'Vulnerability', 'Cyber Attack', 'Security Tools'
            ].map((category) => (
              <TouchableOpacity 
                key={category} 
                onPress={() => handleCategoryPress(category)}
                style={[styles.categoryChip, { 
                  backgroundColor: colors.primary + '18', 
                  borderColor: colors.primary 
                }]}
              >
                <MaterialIcons name="topic" size={14} color={colors.primary} />
                <Text style={[styles.categoryText, { color: colors.primary }]}>{category}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
        <Text style={[styles.tipText, { color: colors.textSecondary }]}>
          Tip: Tap a category above or search for specific threats
        </Text>
      </View>

      {/* Content */}
      {!searchQuery && recentSearches.length > 0 ? (
        /* Recent Searches */
        <View style={styles.recentContainer}>
          <View style={styles.recentHeader}>
            <Text style={[styles.recentTitle, { color: colors.text }]}>Recent Searches</Text>
            <TouchableOpacity onPress={clearRecentSearches}>
              <Text style={[styles.clearText, { color: colors.primary }]}>Clear All</Text>
            </TouchableOpacity>
          </View>
          <ScrollView style={styles.recentList}>
            {recentSearches.map((search, index) => (
              <TouchableOpacity 
                key={index}
                style={[styles.recentItem, { backgroundColor: colors.surface }]}
                onPress={() => handleRecentSearchPress(search)}
              >
                <MaterialIcons name="history" size={20} color={colors.textSecondary} />
                <Text style={[styles.recentItemText, { color: colors.text }]}>{search}</Text>
                <MaterialIcons name="arrow-outward" size={16} color={colors.textSecondary} />
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      ) : (
        /* Search Results or Empty State */
        <FlatList
          data={searchResults}
          keyExtractor={(item, idx) => `search-${item.url}-${idx}`}
          renderItem={({ item }) => <SearchResultItem article={item} />}
          ListEmptyComponent={
            isSearching ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color={colors.primary} />
                <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
                  Searching news...
                </Text>
              </View>
            ) : searchQuery ? (
              <View style={styles.emptyContainer}>
                <MaterialIcons name="search-off" size={64} color={colors.textSecondary} />
                <Text style={[styles.emptyTitle, { color: colors.text }]}>No results found</Text>
                <Text style={[styles.emptySubtitle, { color: colors.textSecondary }]}>
                  Try different keywords or browse categories above
                </Text>
              </View>
            ) : (
              <View style={styles.emptyContainer}>
                <MaterialIcons name="search" size={64} color={colors.textSecondary} />
                <Text style={[styles.emptyTitle, { color: colors.text }]}>Start searching</Text>
                <Text style={[styles.emptySubtitle, { color: colors.textSecondary }]}>
                  Search for cybersecurity news or tap a category above
                </Text>
              </View>
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
          contentContainerStyle={{ paddingBottom: 140 }}
          showsVerticalScrollIndicator={false}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1 
  },
  // Feed-style header
  header: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    justifyContent: 'space-between', 
    padding: 16 
  },
  title: { 
    ...Typography.headlineSmall, 
    fontWeight: '700' 
  },
  refreshBtn: { 
    padding: 8, 
    borderRadius: 12 
  },
  // Feed-style input
  inputRow: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    marginHorizontal: 16, 
    borderWidth: 1, 
    borderRadius: 14, 
    paddingHorizontal: 10, 
    marginBottom: 12 
  },
  input: { 
    flex: 1, 
    paddingVertical: 10, 
    fontSize: 14 
  },
  addButton: { 
    width: 36, 
    height: 36, 
    borderRadius: 10, 
    justifyContent: 'center', 
    alignItems: 'center' 
  },
  // Feed-style categories
  categoriesContainer: { 
    paddingHorizontal: 12, 
    marginBottom: 4 
  },
  categoriesWrap: { 
    marginBottom: 8 
  },
  categoriesScroll: { 
    paddingVertical: 4, 
    gap: 8 
  },
  categoryChip: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    gap: 6, 
    paddingHorizontal: 12, 
    paddingVertical: 6, 
    borderRadius: 18, 
    borderWidth: 1, 
    marginRight: 8 
  },
  categoryText: { 
    fontSize: 11, 
    fontWeight: '600' 
  },
  tipText: { 
    fontSize: 12, 
    marginTop: 6 
  },
  // Recent searches
  recentContainer: {
    flex: 1,
    paddingHorizontal: 16,
  },
  recentHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  recentTitle: {
    ...Typography.headlineSmall,
    fontSize: 18,
    fontWeight: '600',
  },
  clearText: {
    fontSize: 14,
    fontWeight: '500',
  },
  recentList: {
    flex: 1,
  },
  recentItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
    gap: 12,
  },
  recentItemText: {
    flex: 1,
    fontSize: 14,
    fontWeight: '400',
  },
  // Loading and empty states
  loadingContainer: {
    padding: 48,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
  },
  emptyContainer: {
    padding: 48,
    alignItems: 'center',
  },
  emptyTitle: {
    ...Typography.headlineSmall,
    marginTop: 16,
    textAlign: 'center',
  },
  emptySubtitle: {
    ...Typography.body,
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 32,
  },
});
