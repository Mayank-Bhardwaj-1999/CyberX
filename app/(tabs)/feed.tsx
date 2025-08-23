import { useState, useEffect } from 'react';
import { SafeAreaView } from 'react-native-safe-area-context';
import { View, Text, StyleSheet, FlatList, TouchableOpacity, TextInput, Keyboard, ActivityIndicator, RefreshControl, ScrollView } from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';
import { usePersonalFeed } from '../../store/PersonalFeedContext';
import { SearchResultItem } from '../../components/ui/SearchResultItem';
import { UpdateService } from '../../services/updateService';
import { SimpleAnalyticsService } from '../../services/simpleAnalytics';

export default function PersonalFeedScreen() {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const { topics, articles, isLoading, error, addTopic, removeTopic, refresh, lastUpdated } = usePersonalFeed();
  const [input, setInput] = useState('');
  const [adding, setAdding] = useState(false);

  // Track screen view
  useEffect(() => {
    SimpleAnalyticsService.trackScreenView('PersonalFeed', 'PersonalFeedScreen');
  }, []);

  const handleAdd = async () => {
    const v = input.trim();
    if (!v) return;
    setAdding(true);
    
    // Track topic addition
    SimpleAnalyticsService.trackEvent('personal_feed_topic_added', {
      topic: v.substring(0, 50),
      topics_count: topics.length + 1
    });
    
    await addTopic(v);
    setInput('');
    setAdding(false);
    Keyboard.dismiss();
  };

  const sectorSuggestions = [
    { label: 'Information Technology', query: 'software cloud cybersecurity' },
    { label: 'Telecommunications', query: 'telecom ISP 5G network security' },
    { label: 'Energy & Utilities', query: 'power grid energy utility cyber attack' },
    { label: 'Financial Services', query: 'bank fintech payment data breach' },
    { label: 'Healthcare', query: 'hospital healthcare medical device ransomware' },
    { label: 'Government & Defense', query: 'government agency military cyber espionage' },
    { label: 'Transportation & Logistics', query: 'airport airline railway shipping cyber' },
    { label: 'Manufacturing & Industrial', query: 'industrial ICS SCADA factory ransomware' },
    { label: 'Education & Research', query: 'university school research cyber attack' },
    { label: 'Critical Infrastructure', query: 'critical infrastructure public safety emergency systems' },
    { label: 'Media & Entertainment', query: 'media streaming platform social media breach' },
    { label: 'Retail & E-commerce', query: 'retail ecommerce point-of-sale data leak' },
  ];

  const renderTopicChip = (topic: { id: string; label: string; type: string }) => (
    <View key={topic.id} style={[styles.topicChip, { backgroundColor: topic.type==='sector'? colors.security + '18' : colors.primary + '18', borderColor: topic.type==='sector'? colors.security : colors.primary }]}> 
      <Text style={[styles.topicText, { color: topic.type==='sector'? colors.security : colors.primary }]}>{topic.label}</Text>
      <TouchableOpacity onPress={() => removeTopic(topic.id)} style={styles.removeBtn}>
        <MaterialIcons name="close" size={14} color={topic.type==='sector'? colors.security : colors.primary} />
      </TouchableOpacity>
    </View>
  );

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}> 
      <View style={styles.header}> 
        <Text style={[styles.title, { color: colors.text }]}>My Feed v1.1 🚀</Text>
        <View style={styles.header}>
          <TouchableOpacity 
            onPress={() => UpdateService.checkForUpdates()} 
            style={[styles.refreshBtn, { backgroundColor: colors.primaryContainer, marginRight: 8 }]}
          > 
            <MaterialIcons name="system-update" size={18} color={colors.primary} />
          </TouchableOpacity>
          <TouchableOpacity onPress={() => refresh()} style={[styles.refreshBtn, { backgroundColor: colors.primaryContainer }]}> 
            <MaterialIcons name="refresh" size={18} color={colors.primary} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Topic Input */}
      <View style={[styles.inputRow, { borderColor: colors.cardBorder, backgroundColor: colors.surface }]}> 
        <MaterialIcons name="add" size={20} color={colors.primary} />
        <TextInput
          value={input}
          onChangeText={setInput}
          placeholder="Add company, CVE, keyword..."
          placeholderTextColor={colors.textSecondary}
          style={[styles.input, { color: colors.text }]}
          autoCapitalize="none"
          returnKeyType="done"
          onSubmitEditing={handleAdd}
        />
        <TouchableOpacity disabled={!input.trim() || adding} onPress={handleAdd} style={[styles.addButton, { backgroundColor: input.trim() ? colors.primary : colors.surface }]}>
          {adding ? <ActivityIndicator size="small" color={colors.onPrimary} /> : <MaterialIcons name="check" size={18} color={input.trim() ? colors.onPrimary : colors.textSecondary} />}
        </TouchableOpacity>
      </View>
      {error && <Text style={[styles.errorText, { color: colors.error }]}>{error}</Text>}

      {/* Topics list + sector suggestions */}
      <View style={styles.topicsContainer}>
        <View style={styles.topicsWrap}>{topics.map(renderTopicChip)}</View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.sectorScroll}> 
          {sectorSuggestions.map(sec => (
            <TouchableOpacity key={sec.label} onPress={() => addTopic(sec.label, sec.query, 'sector')} style={[styles.sectorChip, { backgroundColor: colors.security + '18', borderColor: colors.security }]}> 
              <MaterialIcons name="domain" size={14} color={colors.security} />
              <Text style={[styles.sectorChipText, { color: colors.security }]}>{sec.label.split(' &')[0]}</Text>
              {topics.some(t=>t.label===sec.label) && (
                <MaterialIcons name="check" size={14} color={colors.security} />
              )}
            </TouchableOpacity>
          ))}
        </ScrollView>
        {topics.length === 0 && (
          <View style={{ marginTop: 8, padding: 12, backgroundColor: colors.primaryContainer + '30', borderRadius: 12, borderWidth: 1, borderColor: colors.primaryContainer }}>
            <Text style={{ color: colors.onPrimaryContainer, fontSize: 13, fontWeight: '600', marginBottom: 4 }}>
              🚀 Get Started with Your Personal Feed
            </Text>
            <Text style={{ color: colors.textSecondary, fontSize: 12, lineHeight: 16 }}>
              Add companies, CVEs, or keywords above, or tap a sector suggestion to start seeing personalized cybersecurity news.
            </Text>
          </View>
        )}
      </View>

      <FlatList
        data={articles}
        keyExtractor={(item, idx) => item.url + idx}
        renderItem={({ item }) => (
          <SearchResultItem article={item} />
        )}
        ListEmptyComponent={isLoading ? (
          <View style={{ padding: 48, alignItems: 'center' }}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={{ color: colors.textSecondary, marginTop: 12 }}>Building personalized feed...</Text>
          </View>
        ) : topics.length > 0 ? (
          <View style={{ padding: 48, alignItems: 'center' }}>
            <Text style={{ color: colors.textSecondary }}>No articles yet. Pull to refresh.</Text>
          </View>
        ) : null}
        refreshControl={<RefreshControl refreshing={isLoading} onRefresh={() => refresh()} colors={[colors.primary]} tintColor={colors.primary} />}
        contentContainerStyle={{ paddingBottom: 140 }}
        showsVerticalScrollIndicator={false}
      />

      {lastUpdated && (
        <Text style={[styles.timestamp, { color: colors.textSecondary }]}>Updated {new Date(lastUpdated).toLocaleTimeString()}</Text>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', padding: 16 },
  title: { ...Typography.headlineSmall, fontWeight: '700' },
  refreshBtn: { padding: 8, borderRadius: 12 },
  inputRow: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, borderWidth: 1, borderRadius: 14, paddingHorizontal: 10, marginBottom: 12 },
  input: { flex: 1, paddingVertical: 10, fontSize: 14 },
  addButton: { width: 36, height: 36, borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  errorText: { marginHorizontal: 16, marginBottom: 8, fontSize: 12 },
  topicsContainer: { paddingHorizontal: 12, marginBottom: 4 },
  topicsWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 8 },
  topicChip: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, borderWidth: 1 },
  topicText: { fontSize: 12, fontWeight: '600', marginRight: 4 },
  removeBtn: { padding: 2 },
  sectorScroll: { paddingVertical: 4, gap: 8 },
  sectorChip: { flexDirection:'row', alignItems:'center', gap:6, paddingHorizontal:12, paddingVertical:6, borderRadius:18, borderWidth:1, marginRight:8 },
  sectorChipText: { fontSize:11, fontWeight:'600' },
  timestamp: { textAlign: 'center', fontSize: 11, marginBottom: 8 },
});
