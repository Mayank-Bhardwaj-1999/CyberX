import React, { useState, useMemo } from 'react';
import {
  View,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  Text,
  FlatList,
} from 'react-native';
import { useTheme } from '../store/ThemeContext';
import { useNews } from '../hooks/useNews';
import { Colors } from '../constants/Colors';
import { Typography } from '../constants/Typography';
import { MaterialIcons } from '@expo/vector-icons';
import { useDebounce } from '../hooks/useDebounce';
import type { Article } from '../types/news';

export function SearchBar() {
  const { theme } = useTheme();
  const colors = Colors[theme === 'auto' ? 'light' : theme];
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const debouncedQuery = useDebounce(searchQuery, 300);

  const { data: news } = useNews('general');

  const searchResults = useMemo(() => {
    if (!debouncedQuery || !news?.articles) return [];

    return news.articles.filter(
      (article) =>
        article.title.toLowerCase().includes(debouncedQuery.toLowerCase()) ||
        article.description?.toLowerCase().includes(debouncedQuery.toLowerCase())
    );
  }, [debouncedQuery, news?.articles]);

  const handleSearch = (text: string) => {
    setSearchQuery(text);
    setIsSearching(!!text);
  };

  const clearSearch = () => {
    setSearchQuery('');
    setIsSearching(false);
  };

  const renderSearchResult = ({ item }: { item: Article }) => (
    <TouchableOpacity
      style={[styles.resultItem, { backgroundColor: colors.background }]}
      onPress={() => {
        // Navigate to article
        clearSearch();
      }}
    >
      <Text style={[styles.resultTitle, { color: colors.text }]} numberOfLines={2}>
        {item.title}
      </Text>
      <Text style={[styles.resultSource, { color: colors.textSecondary }]}>
        {item.source?.name}
      </Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <View style={[styles.searchInput, { backgroundColor: colors.card }]}>
        <MaterialIcons name="search" size={20} color={colors.textSecondary} />
        <TextInput
          style={[styles.input, { color: colors.text }]}
          placeholder="Search news..."
          placeholderTextColor={colors.textSecondary}
          value={searchQuery}
          onChangeText={handleSearch}
          returnKeyType="search"
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={clearSearch}>
            <MaterialIcons name="close" size={20} color={colors.textSecondary} />
          </TouchableOpacity>
        )}
      </View>

      {isSearching && searchResults.length > 0 && (
        <View style={[styles.resultsContainer, { backgroundColor: colors.card }]}>
          <FlatList
            data={searchResults.slice(0, 5)}
            renderItem={renderSearchResult}
            keyExtractor={(item) => item.url}
            ItemSeparatorComponent={() => (
              <View style={[styles.separator, { backgroundColor: colors.border }]} />
            )}
          />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: 20,
    zIndex: 1,
  },
  searchInput: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    gap: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  input: {
    flex: 1,
    ...Typography.body,
    fontSize: 16,
  },
  resultsContainer: {
    position: 'absolute',
    top: 50,
    left: 0,
    right: 0,
    borderRadius: 12,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    maxHeight: 250,
  },
  resultItem: {
    padding: 16,
  },
  resultTitle: {
    ...Typography.body,
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  resultSource: {
    ...Typography.caption,
    fontSize: 12,
  },
  separator: {
    height: 1,
    marginHorizontal: 16,
  },
});
