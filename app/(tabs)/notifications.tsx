import { useState, useEffect } from 'react';
import {
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Text,
  View,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialIcons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useTheme } from '../../store/ThemeContext';
import { useNotifications } from '../../store/NotificationContext';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';
import { SimpleAnalyticsService } from '../../services/simpleAnalytics';
import { feedPushNotificationService } from '../../services/feedNotifications';

export default function NotificationsScreen() {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const { notifications, addNotification, markAsRead, clearNotifications, unreadCount } = useNotifications();
  const [refreshing, setRefreshing] = useState(false);
  
  useEffect(() => {
    SimpleAnalyticsService.trackScreenView('notifications_screen');
    // Set the notification context for feed notifications
    feedPushNotificationService.setNotificationContext(addNotification);
  }, [addNotification]);

  const handleRefresh = async () => {
    setRefreshing(true);
    // Add a sample feed notification for testing
    try {
      addNotification({
        title: "Accenture Acquires CyberCX - Major Cybersecurity Deal",
        source: "Feed Monitor", 
        timestamp: Date.now(),
        kind: 'feed' as const,
        articleUrl: "https://example.com/accenture-cybercx"
      });
      console.log('📱 Added test notification');
    } catch (error) {
      console.error('Error refreshing notifications:', error);
    }
    setTimeout(() => setRefreshing(false), 1000);
    SimpleAnalyticsService.trackEvent('notifications_refresh');
  };

  const handleNotificationPress = (notification: any) => {
    // Mark as read
    markAsRead(notification.id);
    
    SimpleAnalyticsService.trackEvent('notification_opened', { 
      notificationId: notification.id, 
      type: notification.kind || 'news' 
    });

    // Open article if available
    if (notification.articleUrl) {
      router.push({
        pathname: '/article-view/[id]',
        params: { 
          id: encodeURIComponent(notification.articleUrl),
          fromNotification: 'true',
          source: notification.source,
          title: notification.title
        }
      });
    }
  };

  const handleClearAll = () => {
    clearNotifications();
    SimpleAnalyticsService.trackEvent('notifications_cleared');
  };

  const formatTimestamp = (timestamp: number) => {
    const now = Date.now();
    const diff = now - timestamp;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return `${Math.floor(diff / 86400000)}d ago`;
  };

  const getNotificationIcon = (kind?: string) => {
    switch (kind) {
      case 'feed': return 'article';
      case 'threat': return 'security';
      case 'system': return 'settings';
      default: return 'notifications';
    }
  };

  const getNotificationColor = (kind?: string) => {
    switch (kind) {
      case 'feed': return colors.primary;
      case 'threat': return colors.error;
      case 'system': return colors.secondary;
      default: return colors.primary;
    }
  };

  const renderNotification = ({ item }: { item: any }) => (
    <TouchableOpacity
      style={[
        styles.notificationCard,
        { 
          backgroundColor: colors.surface,
          borderLeftColor: item.read ? colors.cardBorder : getNotificationColor(item.kind),
        }
      ]}
      onPress={() => handleNotificationPress(item)}
      activeOpacity={0.7}
    >
      <View style={styles.notificationContent}>
        <View style={styles.notificationHeader}>
          <View style={styles.notificationTypeContainer}>
            <MaterialIcons 
              name={getNotificationIcon(item.kind) as any} 
              size={16} 
              color={getNotificationColor(item.kind)} 
            />
            <Text style={[styles.sourceText, { color: colors.textSecondary }]}>
              {item.source}
            </Text>
          </View>
          <Text style={[styles.timestampText, { color: colors.textSecondary }]}>
            {formatTimestamp(item.timestamp)}
          </Text>
        </View>
        
        <Text 
          style={[
            styles.notificationTitle, 
            { 
              color: colors.text,
              fontWeight: item.read ? '500' : '600'
            }
          ]} 
          numberOfLines={2}
        >
          {item.title}
        </Text>
        
        {/* Show article info if available */}
        {item.articleUrl && (
          <Text 
            style={[styles.notificationDescription, { color: colors.textSecondary }]} 
            numberOfLines={1}
          >
            Tap to read more
          </Text>
        )}
        
        <View style={styles.notificationFooter}>
          <View style={[styles.typeBadge, { backgroundColor: getNotificationColor(item.kind) + '20' }]}>
            <Text style={[styles.typeText, { color: getNotificationColor(item.kind) }]}>
              {(item.kind || 'news').toUpperCase()}
            </Text>
          </View>
          {!item.read && (
            <View style={[styles.unreadIndicator, { backgroundColor: getNotificationColor(item.kind) }]} />
          )}
        </View>
      </View>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={[styles.title, { color: colors.text }]}>Notifications</Text>
        <View style={styles.headerActions}>
          {unreadCount > 0 && (
            <View style={[styles.badge, { backgroundColor: colors.primary }]}>
              <Text style={[styles.badgeText, { color: colors.onPrimary }]}>
                {unreadCount}
              </Text>
            </View>
          )}
        </View>
      </View>

      {/* Content */}
      {notifications.length === 0 ? (
        <View style={styles.emptyState}>
          <MaterialIcons name="notifications-none" size={64} color={colors.textSecondary} />
          <Text style={[styles.emptyTitle, { color: colors.text }]}>
            No notifications yet
          </Text>
          <Text style={[styles.emptySubtitle, { color: colors.textSecondary }]}>
            We'll notify you when there are new cybersecurity updates
          </Text>
          <TouchableOpacity 
            style={[styles.refreshButton, { backgroundColor: colors.primary }]}
            onPress={handleRefresh}
          >
            <Text style={[styles.refreshButtonText, { color: colors.onPrimary }]}>
              Check for Updates
            </Text>
          </TouchableOpacity>
        </View>
      ) : (
        <>
          {/* Clear all button */}
          {notifications.length > 0 && (
            <View style={styles.actions}>
              <TouchableOpacity onPress={handleClearAll} style={styles.clearButton}>
                <Text style={[styles.clearButtonText, { color: colors.textSecondary }]}>
                  Clear All
                </Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Notifications list */}
          <FlatList
            data={notifications}
            renderItem={renderNotification}
            keyExtractor={(item) => item.id}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={handleRefresh}
                colors={[colors.primary]} 
                tintColor={colors.primary} 
              />
            }
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.listContent}
          />
        </>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  title: {
    ...Typography.headlineSmall,
    fontWeight: '700',
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    minWidth: 24,
    alignItems: 'center',
  },
  badgeText: {
    ...Typography.labelSmall,
    fontSize: 12,
    fontWeight: '600',
  },
  actions: {
    paddingHorizontal: 16,
    paddingBottom: 8,
    alignItems: 'flex-end',
  },
  clearButton: {
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  clearButtonText: {
    ...Typography.labelMedium,
    fontSize: 14,
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  notificationCard: {
    borderRadius: 12,
    marginBottom: 12,
    borderLeftWidth: 4,
    overflow: 'hidden',
  },
  notificationContent: {
    padding: 16,
  },
  notificationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  notificationTypeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  sourceText: {
    ...Typography.labelMedium,
    fontSize: 13,
    marginLeft: 6,
    fontWeight: '500',
  },
  timestampText: {
    ...Typography.labelSmall,
    fontSize: 12,
  },
  notificationTitle: {
    ...Typography.titleMedium,
    fontSize: 16,
    lineHeight: 22,
    marginBottom: 4,
  },
  notificationDescription: {
    ...Typography.bodyMedium,
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 12,
  },
  notificationFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  typeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  typeText: {
    ...Typography.labelSmall,
    fontSize: 10,
    fontWeight: '600',
  },
  unreadIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  emptyTitle: {
    ...Typography.headlineSmall,
    fontSize: 22,
    fontWeight: '600',
    marginTop: 16,
    marginBottom: 8,
    textAlign: 'center',
  },
  emptySubtitle: {
    ...Typography.bodyLarge,
    fontSize: 16,
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 32,
  },
  refreshButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
  },
  refreshButtonText: {
    ...Typography.labelLarge,
    fontSize: 16,
    fontWeight: '600',
  },
});
