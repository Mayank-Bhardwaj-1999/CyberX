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
import { useTheme } from '../store/ThemeContext';
import { Colors } from '../constants/Colors';
import { Typography } from '../constants/Typography';
import { MaterialIcons } from '@expo/vector-icons';
import { useDebounce } from '../hooks/useDebounce';
import type { Article } from '../types/news';
import { SearchResultItem } from '../components/ui/SearchResultItem';
import { GoogleNewsService } from '../services/googleNewsService';
import ErrorBoundary from '../components/ui/ErrorBoundary';

export default function SearchScreen() {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Article[]>([]);
  const [defaultArticles, setDefaultArticles] = useState<Article[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoadingDefault, setIsLoadingDefault] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  const debouncedQuery = useDebounce(searchQuery, 500);

  useEffect(() => {
    loadDefaultArticles();
  }, []);

  useEffect(() => {
    if (debouncedQuery) {
      handleSearch(debouncedQuery);
    } else {
      setSearchResults([]);
    }
  }, [debouncedQuery]);

  const loadDefaultArticles = async () => {
    console.log('📰 Loading default cybersecurity news...');
    setIsLoadingDefault(true);
    
    try {
      const articles = await GoogleNewsService.searchCyberSecurityNews('cybersecurity latest news threat', 15);
      setDefaultArticles(articles);
      console.log('✅ Default articles loaded:', articles.length);
    } catch (error) {
      console.error('❌ Error loading default articles:', error);
      // Set some mock articles if the service fails
      const mockArticles: Article[] = [
        {
          title: "Latest Cybersecurity Threats - 2025",
          description: "Stay informed about the latest cybersecurity threats and vulnerabilities affecting organizations worldwide.",
          url: "https://example.com/cyber-threats-2025",
          urlToImage: null,
          publishedAt: new Date().toISOString(),
          source: { id: null, name: "CyberX News" },
          content: "Latest cybersecurity news and updates...",
          author: "CyberX Team",
          summary: "Latest cybersecurity threats and vulnerabilities overview"
        },
        {
          title: "New Malware Campaign Targets Financial Institutions",
          description: "Security researchers have discovered a sophisticated malware campaign targeting major financial institutions.",
          url: "https://example.com/malware-financial",
          urlToImage: null,
          publishedAt: new Date(Date.now() - 3600000).toISOString(),
          source: { id: null, name: "Security Weekly" },
          content: "Financial institutions under attack...",
          author: "Security Analyst",
          summary: "Sophisticated malware campaign targeting banks"
        }
      ];
      setDefaultArticles(mockArticles);
    } finally {
      setIsLoadingDefault(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    if (searchQuery) {
      await handleSearch(searchQuery);
    } else {
      await loadDefaultArticles();
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
      
      // Add to recent searches
      const updatedSearches = [query, ...recentSearches.filter(s => s !== query)].slice(0, 5);
      setRecentSearches(updatedSearches);
    } catch (error) {
      console.error('❌ Search error:', error);
      setSearchResults([]);
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

  return (
    <ErrorBoundary>
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
          <TouchableOpacity onPress={searchQuery ? clearSearch : handleSearchSubmit} style={[styles.addButton, { backgroundColor: colors.primary }]}>
            {isSearching ? (
              <ActivityIndicator size="small" color={colors.onPrimary} />
            ) : (
              <MaterialIcons name={searchQuery ? "close" : "search"} size={18} color={colors.onPrimary} />
            )}
          </TouchableOpacity>
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

        {/* Results */}
        <FlatList
          data={searchQuery ? searchResults : defaultArticles}
          keyExtractor={(item, idx) => `${searchQuery ? 'search' : 'default'}-${item.url}-${idx}`}
          renderItem={({ item }) => <SearchResultItem article={item} />}
          ListEmptyComponent={
            isSearching || isLoadingDefault ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color={colors.primary} />
                <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
                  {isSearching ? 'Searching news...' : 'Loading latest news...'}
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
            ) : null
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
      </SafeAreaView>
    </ErrorBoundary>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1 
  },
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
