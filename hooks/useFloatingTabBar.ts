import { Platform } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

/**
 * Hook to get the appropriate bottom padding to avoid floating tab bar
 */
export function useFloatingTabBarPadding() {
  const insets = useSafeAreaInsets();
  
  // Calculate padding based on floating tab bar height + margins + safe area
  const tabBarHeight = Platform.OS === 'ios' ? 88 : 75;
  const bottomMargin = Platform.OS === 'ios' ? 34 : 16;
  const extraPadding = 8; // Some breathing room
  
  return {
    paddingBottom: tabBarHeight + bottomMargin + insets.bottom + extraPadding,
  };
}

/**
 * Hook to get just the safe area for floating tab bar
 */
export function useFloatingTabBarSafeArea() {
  const insets = useSafeAreaInsets();
  
  return {
    bottom: insets.bottom,
    tabBarSafeHeight: Platform.OS === 'ios' ? 88 + 34 + insets.bottom : 75 + 16 + insets.bottom,
  };
}
