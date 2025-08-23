import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  RefreshControl,
  Alert,
  ScrollView,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useTheme } from '../store/ThemeContext';
import { Colors } from '../constants/Colors';
import { Typography } from '../constants/Typography';
import { formatRelativeTime } from '../utils/dateUtils';
import { getThreatLevelColor } from '../utils/threatAnalysis';
import { useThreatMonitoring } from '../services/threatMonitoring';
import { useNewsMonitor } from '../services/newsMonitor';
import { MaterialCard } from './ui/MaterialComponents';
import { useState, useEffect } from 'react';
import type { ThreatAlert } from '../services/threatMonitoring';

interface RealTimeAlert {
  type: string;
  timestamp: string;
  count: number;
  articles: any[];
  summary: {
    total_new: number;
    sources: string[];
    keywords: string[];
  };
  read?: boolean;
}

export function ThreatAlertsScreen() {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const { alerts, markAsRead } = useThreatMonitoring();
  const { getRecentAlerts, markAlertsAsRead } = useNewsMonitor();
  
  const [realTimeAlerts, setRealTimeAlerts] = useState<RealTimeAlert[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [filterType, setFilterType] = useState('all');

  // Load real-time alerts from backend
  const loadRealTimeAlerts = async () => {
    try {
      const alertData = await getRecentAlerts(1, 50, false);
      if (alertData && alertData.alerts) {
        setRealTimeAlerts(alertData.alerts);
        setUnreadCount(alertData.unreadCount || 0);
      }
    } catch (error) {
      console.log('Failed to load real-time alerts');
    }
  };

  useEffect(() => {
    loadRealTimeAlerts();
    const interval = setInterval(loadRealTimeAlerts, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadRealTimeAlerts();
    setRefreshing(false);
  };

  const getFilteredAlerts = () => {
    const allAlerts = [
      ...realTimeAlerts.map(alert => ({ ...alert, alertType: 'realtime' as const })),
      ...alerts.map(alert => ({ ...alert, alertType: 'threat' as const }))
    ];
    
    switch (filterType) {
      case 'critical':
        return allAlerts.filter(alert => 
          alert.alertType === 'threat' && (alert as any).severity === 'critical'
        );
      case 'high':
        return allAlerts.filter(alert => 
          alert.alertType === 'threat' && (alert as any).severity === 'high'
        );
      case 'unread':
        return allAlerts.filter(alert => !alert.read);
      default:
        return allAlerts;
    }
  };

  const handleRealTimeAlertPress = async (alert: RealTimeAlert) => {
    if (!alert.read) {
      await markAlertsAsRead([alert.timestamp]);
      await loadRealTimeAlerts();
    }
    router.push('/news');
  };

  const handleThreatAlertPress = async (alert: ThreatAlert) => {
    if (!alert.read) {
      await markAsRead(alert.id);
    }
    router.push(`/article-view/${encodeURIComponent(alert.article.url)}`);
  };

  const handleMarkAllAsRead = async () => {
    Alert.alert(
      'Mark All as Read',
      'Are you sure you want to mark all alerts as read?',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Mark All', 
          onPress: async () => {
            await markAlertsAsRead([], true);
            await loadRealTimeAlerts();
          }
        }
      ]
    );
  };

  const renderAlert = ({ item }: { item: any }) => {
    const isRealTime = item.alertType === 'realtime';
    
    if (isRealTime) {
      return (
        <MaterialCard
          variant="outlined"
          onPress={() => handleRealTimeAlertPress(item)}
          style={[
            styles.alertCard,
            !item.read && { backgroundColor: colors.primaryContainer + '20' }
          ]}
        >
          <View style={styles.alertContent}>
            <View style={styles.alertHeader}>
              <View style={styles.alertIndicator}>
                <View style={[styles.severityDot, { backgroundColor: colors.primary }]} />
                <Feather name="bell" size={18} color={colors.primary} />
              </View>
              <View style={styles.alertInfo}>
                <Text style={[styles.severityText, { color: colors.primary }]}>
                  NEW ARTICLES
                </Text>
                <Text style={[styles.timestampText, { color: colors.textSecondary }]}>
                  {formatRelativeTime(item.timestamp)}
                </Text>
              </View>
              <View style={styles.riskScoreContainer}>
                <Text style={[styles.riskScore, { color: colors.text }]}>
                  {item.count}
                </Text>
                <Text style={[styles.riskLabel, { color: colors.textSecondary }]}>
                  Articles
                </Text>
              </View>
            </View>
            <Text style={[styles.alertTitle, { color: colors.text }]} numberOfLines={2}>
              {item.summary?.keywords?.slice(0, 3).join(', ') || 'New cybersecurity articles available'}
            </Text>
            <Text style={[styles.alertDescription, { color: colors.textSecondary }]} numberOfLines={3}>
              {item.summary?.sources?.slice(0, 2).join(', ') || 'Multiple sources'}
            </Text>
          </View>
        </MaterialCard>
      );
    } else {
      const threatAlert = item as ThreatAlert;
      return (
        <MaterialCard
          variant="outlined"
          onPress={() => handleThreatAlertPress(threatAlert)}
          style={[
            styles.alertCard,
            !threatAlert.read && { backgroundColor: colors.errorContainer + '20' }
          ]}
        >
          <View style={styles.alertContent}>
            <View style={styles.alertHeader}>
              <View style={styles.alertIndicator}>
                <View style={[styles.severityDot, { backgroundColor: getThreatLevelColor(threatAlert.severity, colors) }]} />
                <Feather 
                  name={threatAlert.severity === 'critical' ? 'alert-circle' : threatAlert.severity === 'high' ? 'alert-triangle' : 'info'}
                  size={18} 
                  color={getThreatLevelColor(threatAlert.severity, colors)} 
                />
              </View>
              <View style={styles.alertInfo}>
                <Text style={[styles.severityText, { color: getThreatLevelColor(threatAlert.severity, colors) }]}>
                  {threatAlert.severity.toUpperCase()} THREAT
                </Text>
                <Text style={[styles.timestampText, { color: colors.textSecondary }]}>
                  {formatRelativeTime(threatAlert.timestamp)}
                </Text>
              </View>
              <View style={styles.riskScoreContainer}>
                <Text style={[styles.riskScore, { color: colors.text }]}>
                  {threatAlert.riskScore}
                </Text>
                <Text style={[styles.riskLabel, { color: colors.textSecondary }]}>
                  Risk
                </Text>
              </View>
            </View>
            <Text style={[styles.alertTitle, { color: colors.text }]} numberOfLines={2}>
              {threatAlert.article.title}
            </Text>
            <Text style={[styles.alertDescription, { color: colors.textSecondary }]} numberOfLines={3}>
              {threatAlert.description}
            </Text>
          </View>
        </MaterialCard>
      );
    }
  };

  const totalUnreadCount = unreadCount + alerts.filter(alert => !alert.read).length;
  const filteredAlerts = getFilteredAlerts();

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.text }]}>Threat Alerts</Text>
        <View style={styles.headerActions}>
          {totalUnreadCount > 0 && (
            <TouchableOpacity onPress={handleMarkAllAsRead} style={[styles.markAllBtn, { backgroundColor: colors.primaryContainer }]}>
              <Feather name="check" size={16} color={colors.primary} />
              <Text style={[styles.markAllText, { color: colors.primary }]}>Mark All</Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity onPress={handleRefresh} style={[styles.refreshBtn, { backgroundColor: colors.primaryContainer }]}>
            <Feather name="refresh-cw" size={18} color={colors.primary} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Filter Chips */}
      <View style={styles.filtersContainer}>
        <View style={styles.filtersWrap}>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filtersScroll}>
            {[
              { id: 'all', label: 'All Alerts', icon: 'shield' },
              { id: 'critical', label: 'Critical', icon: 'alert-circle' },
              { id: 'high', label: 'High', icon: 'alert-triangle' },
              { id: 'unread', label: 'Unread', icon: 'bell' }
            ].map((filter) => (
              <TouchableOpacity 
                key={filter.id} 
                onPress={() => setFilterType(filter.id)}
                style={[styles.filterChip, { 
                  backgroundColor: filterType === filter.id ? colors.primary + '18' : colors.surface, 
                  borderColor: filterType === filter.id ? colors.primary : colors.cardBorder
                }]}
              >
                <Feather name={filter.icon as any} size={14} color={filterType === filter.id ? colors.primary : colors.textSecondary} />
                <Text style={[styles.filterText, { 
                  color: filterType === filter.id ? colors.primary : colors.textSecondary 
                }]}>
                  {filter.label}
                </Text>
                {filter.id === 'unread' && totalUnreadCount > 0 && (
                  <View style={[styles.filterBadge, { backgroundColor: colors.error }]}>
                    <Text style={[styles.filterBadgeText, { color: colors.onError }]}>
                      {totalUnreadCount > 9 ? '9+' : totalUnreadCount}
                    </Text>
                  </View>
                )}
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
        <Text style={[styles.tipText, { color: colors.textSecondary }]}>
          Tap filters to view specific alert types
        </Text>
      </View>

      {/* Alerts List */}
      {filteredAlerts.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Feather name="shield-check" size={64} color={colors.textSecondary} />
          <Text style={[styles.emptyTitle, { color: colors.text }]}>
            {filterType === 'all' ? 'No Alerts' : `No ${filterType} alerts`}
          </Text>
          <Text style={[styles.emptySubtitle, { color: colors.textSecondary }]}>
            You'll be notified when new cybersecurity threats are detected
          </Text>
        </View>
      ) : (
        <FlatList
          data={filteredAlerts}
          keyExtractor={(item, index) => `${item.alertType}-${item.timestamp || (item as any).id}-${index}`}
          renderItem={renderAlert}
          contentContainerStyle={{ paddingBottom: 140 }}
          showsVerticalScrollIndicator={false}
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
  markAllBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 6,
    borderRadius: 12,
  },
  markAllText: {
    fontSize: 12,
    fontWeight: '600',
  },
  refreshBtn: { 
    padding: 8, 
    borderRadius: 12 
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
  filterBadge: {
    minWidth: 16,
    height: 16,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 4,
  },
  filterBadgeText: {
    fontSize: 10,
    fontWeight: '600',
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
  // Alert cards
  alertCard: {
    marginHorizontal: 16,
    marginVertical: 4,
  },
  alertContent: {
    padding: 16,
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  alertIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginRight: 12,
  },
  severityDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  alertInfo: {
    flex: 1,
  },
  severityText: {
    fontSize: 12,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  timestampText: {
    fontSize: 12,
    marginTop: 2,
  },
  riskScoreContainer: {
    alignItems: 'center',
    minWidth: 40,
  },
  riskScore: {
    fontSize: 18,
    fontWeight: '700',
  },
  riskLabel: {
    fontSize: 10,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  alertTitle: {
    ...Typography.titleMedium,
    marginBottom: 8,
    lineHeight: 20,
  },
  alertDescription: {
    ...Typography.body,
    lineHeight: 18,
  },
});
