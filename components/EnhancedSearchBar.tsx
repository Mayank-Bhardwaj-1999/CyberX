import { useState, useMemo } from 'react';
import {
  View,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  Text,
  FlatList,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useTheme } from '../store/ThemeContext';
import { useNews } from '../hooks/useNews';
import { Colors } from '../constants/Colors';
import { Typography } from '../constants/Typography';
import { useDebounce } from '../hooks/useDebounce';
import { MaterialCard, MaterialElevation } from './ui/MaterialComponents';
import type { Article } from '../types/news';

interface EnhancedSearchBarProps {
  placeholder?: string;
  onSearchFocus?: () => void;
  onSearchBlur?: () => void;
  showSuggestions?: boolean;
}

export function EnhancedSearchBar({ 
  placeholder = "Search cybersecurity news...",
  onSearchFocus,
  onSearchBlur,
  showSuggestions = true
}: EnhancedSearchBarProps) {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const debouncedQuery = useDebounce(searchQuery, 300);

  const { articles: newsArticles } = useNews('general');

  const searchResults = useMemo(() => {
    if (!debouncedQuery || !newsArticles) return [];

    return newsArticles.filter(
      (article: Article) =>
        article.title.toLowerCase().includes(debouncedQuery.toLowerCase()) ||
        article.description?.toLowerCase().includes(debouncedQuery.toLowerCase())
    ).slice(0, 5); // Limit to 5 results for better UX
  }, [debouncedQuery, newsArticles]);

  const handleSearch = (text: string) => {
    setSearchQuery(text);
    setIsSearching(!!text);
  };

  const clearSearch = () => {
    setSearchQuery('');
    setIsSearching(false);
  };

  const handleFocus = () => {
    setIsFocused(true);
    onSearchFocus?.();
  };

  const handleBlur = () => {
    setIsFocused(false);
    onSearchBlur?.();
  };

  const navigateToArticle = (article: Article) => {
    router.push(`/article-view/${encodeURIComponent(article.url)}`);
    clearSearch();
  };

  const renderSearchResult = ({ item }: { item: Article }) => (
    <MaterialCard 
      variant="outlined" 
      onPress={() => navigateToArticle(item)}
      style={styles.resultItem}
    >
      <View style={styles.resultContent}>
        <View style={styles.resultIconContainer}>
          <Feather name="file-text" size={16} color={colors.textSecondary} />
        </View>
        <View style={styles.resultTextContainer}>
          <Text style={[Typography.cardTitle, { color: colors.text }]} numberOfLines={2}>
            {item.title}
          </Text>
          <Text style={[Typography.cardSubtitle, { color: colors.textSecondary }]} numberOfLines={1}>
            {item.source.name}
          </Text>
        </View>
      </View>
    </MaterialCard>
  );

  const renderSuggestionChips = () => {
    const suggestions = ['Malware', 'Data Breach', 'Vulnerability', 'Ransomware', 'Phishing'];
    
    return (
      <View style={styles.suggestionsContainer}>
        <Text style={[Typography.labelMedium, { color: colors.textSecondary, marginBottom: 12 }]}>
          TRENDING TOPICS
        </Text>
        <View style={styles.chipsContainer}>
          {suggestions.map((suggestion, index) => (
            <TouchableOpacity
              key={index}
              style={[styles.suggestionChip, { backgroundColor: colors.primaryContainer }]}
              onPress={() => handleSearch(suggestion)}
            >
              <Text style={[Typography.labelMedium, { color: colors.onPrimaryContainer }]}>
                {suggestion}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Search Input Container */}
      <MaterialElevation 
        level={isFocused ? 3 : 1} 
        style={[
          styles.searchContainer,
          { 
            backgroundColor: colors.surfaceContainer,
            borderColor: isFocused ? colors.primary : colors.outline,
            borderWidth: isFocused ? 2 : 1,
          }
        ]}
      >
        <View style={styles.searchInputContainer}>
          <Feather 
            name="search" 
            size={20} 
            color={isFocused ? colors.primary : colors.textSecondary} 
            style={styles.searchIcon}
          />
          
          <TextInput
            style={[
              Typography.bodyLarge,
              styles.searchInput,
              { color: colors.text }
            ]}
            placeholder={placeholder}
            placeholderTextColor={colors.textTertiary}
            value={searchQuery}
            onChangeText={handleSearch}
            onFocus={handleFocus}
            onBlur={handleBlur}
            returnKeyType="search"
            autoCorrect={false}
            autoCapitalize="none"
          />

          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={clearSearch} style={styles.clearButton}>
              <Feather name="x" size={18} color={colors.textSecondary} />
            </TouchableOpacity>
          )}
        </View>
      </MaterialElevation>

      {/* Search Results or Suggestions */}
      {isSearching && searchQuery.length > 0 ? (
        searchResults.length > 0 ? (
          <MaterialCard variant="elevated" style={styles.resultsContainer}>
            <FlatList
              data={searchResults}
              renderItem={renderSearchResult}
              keyExtractor={(item, index) => `${item.url}-${index}`}
              showsVerticalScrollIndicator={false}
              ItemSeparatorComponent={() => <View style={styles.resultSeparator} />}
            />
            
            <TouchableOpacity 
              style={[styles.viewAllButton, { backgroundColor: colors.primary }]}
              onPress={() => router.push(`/search?q=${encodeURIComponent(searchQuery)}`)}
            >
              <Text style={[Typography.labelLarge, { color: colors.onPrimary }]}>
                View All Results
              </Text>
              <Feather name="arrow-right" size={16} color={colors.onPrimary} />
            </TouchableOpacity>
          </MaterialCard>
        ) : (
          <MaterialCard variant="outlined" style={styles.noResultsContainer}>
            <View style={styles.noResultsContent}>
              <Feather name="search" size={48} color={colors.textTertiary} />
              <Text style={[Typography.titleMedium, { color: colors.textSecondary, marginTop: 16 }]}>
                No results found
              </Text>
              <Text style={[Typography.bodyMedium, { color: colors.textTertiary, marginTop: 8 }]}>
                Try different keywords or browse latest news
              </Text>
            </View>
          </MaterialCard>
        )
      ) : (
        showSuggestions && isFocused && renderSuggestionChips()
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginVertical: 8,
  },
  searchContainer: {
    borderRadius: 28,
    overflow: 'hidden',
  },
  searchInputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  searchIcon: {
    marginRight: 12,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    paddingVertical: 4,
  },
  clearButton: {
    padding: 4,
    marginLeft: 8,
  },
  resultsContainer: {
    marginTop: 8,
    maxHeight: 300,
    padding: 8,
  },
  resultItem: {
    padding: 12,
    marginVertical: 2,
  },
  resultContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  resultIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
    backgroundColor: 'rgba(99, 102, 241, 0.1)',
  },
  resultTextContainer: {
    flex: 1,
  },
  resultSeparator: {
    height: 1,
    backgroundColor: 'rgba(0,0,0,0.05)',
    marginVertical: 4,
  },
  viewAllButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 24,
    marginTop: 8,
    gap: 8,
  },
  noResultsContainer: {
    marginTop: 8,
    padding: 32,
  },
  noResultsContent: {
    alignItems: 'center',
  },
  suggestionsContainer: {
    marginTop: 16,
    padding: 16,
  },
  chipsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  suggestionChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 8,
  },
});
