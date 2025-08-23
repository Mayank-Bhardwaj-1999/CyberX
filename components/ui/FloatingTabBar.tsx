import { View, StyleSheet } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';

interface FloatingTabBarBackgroundProps {
  children: React.ReactNode;
}

export function FloatingTabBarBackground({ children }: FloatingTabBarBackgroundProps) {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const insets = useSafeAreaInsets();

  return (
    <View style={[
      styles.container,
      {
        backgroundColor: colors.surface,
        marginBottom: insets.bottom,
      }
    ]}>
      <View style={[
        styles.innerContainer,
        {
          backgroundColor: colors.surface,
          shadowColor: colors.shadow,
          borderColor: colors.outline + '20',
        }
      ]}>
        {children}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 16,
    left: 16,
    right: 16,
    borderRadius: 24,
    overflow: 'hidden',
  },
  innerContainer: {
    borderRadius: 24,
    borderWidth: 1,
    shadowOffset: {
      width: 0,
      height: 8,
    },
    shadowOpacity: 0.25,
    shadowRadius: 16,
    elevation: 12,
    // Add backdrop blur effect
    backdropFilter: 'blur(20px)',
  },
});
