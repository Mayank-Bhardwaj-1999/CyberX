import {
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ScrollView,
  Text,
  View,
  TextInput,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialIcons } from '@expo/vector-icons';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';
import { useBookmarks } from '../../hooks/useBookmarks';
import { SearchResultItem } from '../../components/ui/SearchResultItem';
import type { Article } from '../../types/news';
import { useState } from 'react';

export default function BookmarksScreen() {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const { bookmarks } = useBookmarks();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [refreshing, setRefreshing] = useState(false);

  const handleRefresh = async () => {
    setRefreshing(true);
    // Simulate refresh - bookmarks are already reactive
    setTimeout(() => setRefreshing(false), 500);
  };

  const handleClearAll = () => {
    // For now, just show an alert - you can implement actual clear functionality
    console.log('Clear all bookmarks requested');
  };

  const getFilteredBookmarks = () => {
    let filtered = bookmarks;
    
    if (searchQuery) {
      filtered = filtered.filter(article => 
        article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (article.description && article.description.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    switch (filterType) {
      case 'recent':
        return filtered.slice(0, 10); // Show recent 10
      case 'older':
        return filtered.slice(10); // Show older than 10
      default:
        return filtered;
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
  };

  const filteredBookmarks = getFilteredBookmarks();

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.text }]}>Saved Articles</Text>
        <View style={styles.headerActions}>
          {bookmarks.length > 0 && (
            <TouchableOpacity onPress={handleClearAll} style={[styles.clearBtn, { backgroundColor: colors.errorContainer }]}>
              <MaterialIcons name="clear-all" size={16} color={colors.error} />
              <Text style={[styles.clearText, { color: colors.error }]}>Clear</Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity onPress={handleRefresh} style={[styles.refreshBtn, { backgroundColor: colors.primaryContainer }]}>
            <MaterialIcons name="refresh" size={18} color={colors.primary} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Search Input */}
      <View style={[styles.inputRow, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}>
        <MaterialIcons name="search" size={20} color={colors.primary} />
        <TextInput
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholder="Search saved articles..."
          placeholderTextColor={colors.textSecondary}
          style={[styles.input, { color: colors.text }]}
          autoCapitalize="none"
          returnKeyType="search"
        />
        <TouchableOpacity onPress={clearSearch} style={[styles.addButton, { backgroundColor: searchQuery ? colors.primary : colors.surface }]}>
          <MaterialIcons name="close" size={18} color={searchQuery ? colors.onPrimary : colors.textSecondary} />
        </TouchableOpacity>
      </View>

      {/* Filter Chips */}
      <View style={styles.filtersContainer}>
        <View style={styles.filtersWrap}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filtersScroll}>
            {[
              { id: 'all', label: `All (${bookmarks.length})`, icon: 'bookmark' as const },
              { id: 'recent', label: 'Recent', icon: 'schedule' as const },
              { id: 'older', label: 'Older', icon: 'history' as const }
            ].map((filter) => (
              <TouchableOpacity 
                key={filter.id} 
                onPress={() => setFilterType(filter.id)}
                style={[styles.filterChip, { 
                  backgroundColor: filterType === filter.id ? colors.primary + '18' : colors.surface, 
                  borderColor: filterType === filter.id ? colors.primary : colors.cardBorder
                }]}
              >
                <MaterialIcons name={filter.icon} size={14} color={filterType === filter.id ? colors.primary : colors.textSecondary} />
                <Text style={[styles.filterText, { 
                  color: filterType === filter.id ? colors.primary : colors.textSecondary 
                }]}>
                  {filter.label}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
        <Text style={[styles.tipText, { color: colors.textSecondary }]}>
          Tip: Use search or filters to find specific saved articles
        </Text>
      </View>

      {/* Bookmarks List */}
      {filteredBookmarks.length === 0 ? (
        <View style={styles.emptyContainer}>
          <MaterialIcons name={bookmarks.length === 0 ? "bookmark-border" : "search-off"} size={64} color={colors.textSecondary} />
          <Text style={[styles.emptyTitle, { color: colors.text }]}>
            {bookmarks.length === 0 ? 'No saved articles' : 'No results found'}
          </Text>
          <Text style={[styles.emptySubtitle, { color: colors.textSecondary }]}>
            {bookmarks.length === 0 
              ? 'Save articles by tapping the bookmark icon' 
              : 'Try adjusting your search or filter settings'
            }
          </Text>
        </View>
      ) : (
        <FlatList
          data={filteredBookmarks}
          renderItem={({ item }) => <SearchResultItem article={item} />}
          keyExtractor={(item) => item.url}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={{ paddingBottom: 140 }}
          refreshControl={
            <RefreshControl 
              refreshing={refreshing} 
              onRefresh={handleRefresh} 
              colors={[colors.primary]} 
              tintColor={colors.primary} 
            />
          }
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
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  clearBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderRadius: 12,
  },
  clearText: {
    fontSize: 12,
    fontWeight: '600',
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
  // Feed-style filters
  filtersContainer: { 
    paddingHorizontal: 12, 
    marginBottom: 4 
  },
  filtersWrap: { 
    marginBottom: 8 
  },
  filtersScroll: { 
    paddingVertical: 4, 
    gap: 8 
  },
  filterChip: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    gap: 6, 
    paddingHorizontal: 12, 
    paddingVertical: 6, 
    borderRadius: 18, 
    borderWidth: 1, 
    marginRight: 8 
  },
  filterText: { 
    fontSize: 11, 
    fontWeight: '600' 
  },
  tipText: { 
    fontSize: 12, 
    marginTop: 6 
  },
  // Empty state
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 48,
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
