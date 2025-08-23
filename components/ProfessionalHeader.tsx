import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { Feather } from '@expo/vector-icons';
import { useTheme } from '../store/ThemeContext';
import { Colors } from '../constants/Colors';
import { Typography } from '../constants/Typography';
import { MaterialElevation } from './ui/MaterialComponents';
import { ThemeToggle } from './ThemeToggle';
import { getNetworkStatus, subscribeToNetworkStatus, NetworkStatus } from '../utils/networkTest';

interface ProfessionalHeaderProps {
  title: string;
  subtitle?: string;
  showGradient?: boolean;
  elevation?: 0 | 1 | 2 | 3 | 4 | 5;
}

export function ProfessionalHeader({ 
  title, 
  subtitle, 
  showGradient = true,
  elevation = 2 
}: ProfessionalHeaderProps) {
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

  const headerContent = (
    <View style={[styles.container, { paddingTop: insets.top + 8 }]}>
      <View style={styles.content}>
        <View style={styles.titleSection}>
          <MaterialElevation level={3} style={[styles.iconContainer, { backgroundColor: colors.primary }]}>
            <Feather name="shield" size={24} color={colors.onPrimary} />
          </MaterialElevation>
          
          <View style={styles.textContainer}>
            <View style={styles.titleRow}>
              <Text style={[Typography.headlineMedium, { color: showGradient ? colors.onPrimary : colors.text }]}>
                {title}
              </Text>
              <View style={styles.rightSection}>
                <View style={styles.themeToggleContainer}>
                  <ThemeToggle size={20} />
                </View>
                <View style={styles.statusIndicator}>
                  <Feather 
                    name={networkStatus.isConnected ? "wifi" : "wifi-off"} 
                    size={8} 
                    color={colors.onPrimary} 
                  />
                  <Text style={[Typography.labelSmall, { color: colors.onPrimary, marginLeft: 4, fontSize: 10 }]}>
                    {networkStatus.isConnected ? "LIVE" : "OFFLINE"}
                  </Text>
                </View>
              </View>
            </View>
            {subtitle && (
              <Text style={[Typography.bodyLarge, { 
                color: showGradient ? colors.onPrimary : colors.textSecondary,
                opacity: 0.9,
                marginTop: 4 
              }]}>
                {subtitle}
              </Text>
            )}
          </View>
        </View>
      </View>
    </View>
  );

  if (showGradient) {
    return (
      <MaterialElevation level={elevation} style={styles.wrapper}>
        <LinearGradient
          colors={[colors.primary, colors.secondary]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.gradientContainer}
        >
          {headerContent}
        </LinearGradient>
      </MaterialElevation>
    );
  }

  return (
    <MaterialElevation level={elevation} style={[styles.wrapper, { backgroundColor: colors.surface }]}>
      {headerContent}
    </MaterialElevation>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
    overflow: 'hidden',
  },
  gradientContainer: {
    flex: 1,
  },
  container: {
    minHeight: 120,
  },
  content: {
    paddingHorizontal: 20,
    paddingBottom: 24,
    flex: 1,
    justifyContent: 'space-between',
  },
  titleSection: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  iconContainer: {
    width: 56,
    height: 56,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.3,
    shadowRadius: 8,
  },
  textContainer: {
    flex: 1,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  rightSection: {
    alignItems: 'flex-end',
    gap: 6,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  statusIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.1)', // Dynamic background based on network status
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 1,
    },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 1,
    minWidth: 50,
    justifyContent: 'center',
  },
  themeToggleContainer: {
    marginBottom: 2,
  },
});