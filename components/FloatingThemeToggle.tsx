import { View, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { ThemeToggle } from './ThemeToggle';

interface FloatingThemeToggleProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
}

export function FloatingThemeToggle({ position = 'top-right' }: FloatingThemeToggleProps) {
  const insets = useSafeAreaInsets();
  
  const getPositionStyle = () => {
    const baseMargin = 16;
    
    switch (position) {
      case 'top-right':
        return {
          position: 'absolute' as const,
          top: insets.top + baseMargin,
          right: baseMargin,
        };
      case 'top-left':
        return {
          position: 'absolute' as const,
          top: insets.top + baseMargin,
          left: baseMargin,
        };
      case 'bottom-right':
        return {
          position: 'absolute' as const,
          bottom: insets.bottom + baseMargin,
          right: baseMargin,
        };
      case 'bottom-left':
        return {
          position: 'absolute' as const,
          bottom: insets.bottom + baseMargin,
          left: baseMargin,
        };
      default:
        return {
          position: 'absolute' as const,
          top: insets.top + baseMargin,
          right: baseMargin,
        };
    }
  };

  return (
    <View style={[styles.container, getPositionStyle()]}>
      <ThemeToggle size={22} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    zIndex: 1000,
    elevation: 10,
  },
});
