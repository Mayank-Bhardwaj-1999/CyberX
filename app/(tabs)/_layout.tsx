import { Tabs } from 'expo-router';
import { MaterialIcons } from '@expo/vector-icons';
import { useTheme } from '../../store/ThemeContext';
import { useNotifications } from '../../store/NotificationContext';
import { Colors } from '../../constants/Colors';
import { Platform } from 'react-native';

export default function TabLayout() {
  const { resolvedTheme } = useTheme();
  const { unreadCount } = useNotifications();
  const colors = Colors[resolvedTheme] || Colors.dark;

  // Modern floating tab bar dimensions
  const tabBarHeight = Platform.OS === 'ios' ? 88 : 75;
  const iconSize = 24;

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
        tabBarStyle: {
          backgroundColor: resolvedTheme === 'dark' ? colors.surface + 'F0' : colors.surface + 'F8',
          borderTopWidth: 0,
          height: tabBarHeight,
          paddingBottom: Platform.OS === 'ios' ? 28 : 15,
          paddingTop: 10,
          paddingHorizontal: 8,
          marginHorizontal: 16,
          marginBottom: Platform.OS === 'ios' ? 34 : 16,
          borderRadius: 28,
          shadowColor: resolvedTheme === 'dark' ? '#000' : '#000',
          shadowOffset: {
            width: 0,
            height: 8,
          },
          shadowOpacity: resolvedTheme === 'dark' ? 0.4 : 0.15,
          shadowRadius: 16,
          elevation: 12,
          position: 'absolute',
          left: 0,
          right: 0,
          bottom: 0,
          // Add a subtle border for definition
          borderWidth: resolvedTheme === 'dark' ? 1 : 0.5,
          borderColor: resolvedTheme === 'dark' ? colors.outline + '40' : colors.outline + '20',
        },
        headerShown: false,
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
          marginTop: 4,
          fontFamily: 'Inter-SemiBold',
        },
        tabBarItemStyle: {
          borderRadius: 20,
          marginHorizontal: 2,
          paddingVertical: 4,
          // Add subtle highlight for active state
          backgroundColor: 'transparent',
        },
        // Custom active background
        tabBarActiveBackgroundColor: colors.primaryContainer + '30',
      }}
    >
      {/* Main Navigation Tabs - Clean 4-tab design */}
      <Tabs.Screen
        name="news"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, focused }) => (
            <MaterialIcons 
              name="home" 
              size={iconSize} 
              color={focused ? colors.primary : color} 
            />
          ),
        }}
      />
      <Tabs.Screen
        name="search"
        options={{
          title: 'Search',
          tabBarIcon: ({ color, focused }) => (
            <MaterialIcons 
              name="search" 
              size={iconSize} 
              color={focused ? colors.primary : color} 
            />
          ),
        }}
      />
      <Tabs.Screen
        name="feed"
        options={{
          title: 'Feed',
          tabBarIcon: ({ color, focused }) => (
            <MaterialIcons
              name="dynamic-feed"
              size={iconSize}
              color={focused ? colors.primary : color}
            />
          ),
        }}
      />
      <Tabs.Screen
        name="notifications"
        options={{
          title: 'Notifications',
          tabBarIcon: ({ color, focused }) => (
            <MaterialIcons 
              name="notifications" 
              size={iconSize} 
              color={focused ? colors.primary : color} 
            />
          ),
          tabBarBadge: unreadCount > 0 ? unreadCount : undefined,
          tabBarBadgeStyle: {
            backgroundColor: colors.error,
            color: colors.onError,
            fontSize: 10,
            fontWeight: '700',
            minWidth: 18,
            height: 18,
            borderRadius: 9,
            borderWidth: 2,
            borderColor: colors.surface,
          },
        }}
      />
      <Tabs.Screen
        name="bookmarks"
        options={{
          title: 'Saved',
          tabBarIcon: ({ color, focused }) => (
            <MaterialIcons 
              name={focused ? 'bookmark' : 'bookmark-border'} 
              size={iconSize} 
              color={focused ? colors.primary : color} 
            />
          ),
        }}
      />
      
      {/* Hide saved tab if it exists */}
      <Tabs.Screen
        name="saved"
        options={{
          href: null, // This completely hides the tab
        }}
      />
      
      {/* Hide enhanced-news tab if it exists */}
      <Tabs.Screen
        name="enhanced-news"
        options={{
          href: null, // This completely hides the tab
        }}
      />
    </Tabs>
  );
}
