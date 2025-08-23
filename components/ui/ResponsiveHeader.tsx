import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { MaterialIcons } from '@expo/vector-icons';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';
import { getNetworkStatus, subscribeToNetworkStatus, NetworkStatus } from '../../utils/networkTest';

const { width } = Dimensions.get('window');
const isSmallScreen = width < 375; // iPhone SE and smaller

interface ResponsiveHeaderProps {
  title: string;
  showBadge?: boolean;
  badgeCount?: number;
  actions?: React.ReactNode;
}

export function ResponsiveHeader({ 
  title, 
  showBadge = false,
  badgeCount = 0,
  actions
}: ResponsiveHeaderProps) {
  const insets = useSafeAreaInsets();
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const [networkStatus, setNetworkStatus] = React.useState<NetworkStatus>({
    isConnected: false,
    connectionType: null,
    isInternetReachable: false,
  });

  React.useEffect(() => {
    // Get initial network status
    getNetworkStatus().then(setNetworkStatus);
    
    // Subscribe to network changes
    const unsubscribe = subscribeToNetworkStatus(setNetworkStatus);
    
    return unsubscribe;
  }, []);

  // Responsive padding based on screen size
  const responsivePadding = isSmallScreen ? 12 : 16;
  const responsiveTop = isSmallScreen ? insets.top + 4 : insets.top + 8;

  return (
    <View style={[
      styles.container, 
      { 
        backgroundColor: colors.background,
        paddingTop: responsiveTop,
        paddingBottom: responsivePadding,
        paddingHorizontal: responsivePadding,
      }
    ]}>
      <View style={styles.headerContent}>
        <View style={styles.titleSection}>
          <MaterialIcons 
            name={title === "Notifications" ? "notifications" : "bookmark"} 
            size={isSmallScreen ? 18 : 20} 
            color={colors.primary} 
          />
          <Text style={[
            styles.title, 
            { 
              color: colors.text,
              fontSize: isSmallScreen ? 18 : 20
            }
          ]}>
            {title}
          </Text>
          {showBadge && badgeCount > 0 && (
            <View style={[styles.badge, { backgroundColor: colors.primary }]}>
              <Text style={styles.badgeText}>{badgeCount}</Text>
            </View>
          )}
        </View>

        <View style={styles.statusSection}>
          {actions && (
            <View style={styles.actionsContainer}>
              {actions}
            </View>
          )}
          <View style={[
            styles.statusIndicator, 
            { 
              backgroundColor: networkStatus.isConnected 
                ? 'rgba(34, 197, 94, 0.15)' 
                : 'rgba(239, 68, 68, 0.15)'
            }
          ]}>
            <MaterialIcons 
              name={networkStatus.isConnected ? "wifi" : "wifi-off"} 
              size={isSmallScreen ? 8 : 10} 
              color={networkStatus.isConnected ? '#22C55E' : '#EF4444'} 
            />
            <Text style={[
              styles.statusText, 
              { 
                color: networkStatus.isConnected ? '#22C55E' : '#EF4444',
                fontSize: isSmallScreen ? 8 : 9
              }
            ]}>
              {networkStatus.isConnected ? "LIVE" : "OFFLINE"}
            </Text>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.05)',
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  titleSection: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 10,
  },
  title: {
    ...Typography.headlineSmall,
    fontWeight: '700',
  },
  badge: {
    minWidth: 18,
    height: 18,
    borderRadius: 9,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 6,
  },
  badgeText: {
    ...Typography.labelSmall,
    fontSize: 9,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  statusSection: {
    alignItems: 'flex-end',
    flexDirection: 'row',
    gap: 8,
  },
  actionsContainer: {
    flexDirection: 'row',
    gap: 6,
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 10,
    gap: 3,
    minWidth: 45,
    justifyContent: 'center',
  },
  statusText: {
    fontWeight: '700',
    fontSize: 9,
  },
});
