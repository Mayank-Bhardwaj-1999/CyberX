import { TouchableOpacity, StyleSheet } from 'react-native';
import { useTheme } from '../store/ThemeContext';
import { Colors } from '../constants/Colors';
import { SafeMaterialIcon } from './ui/SafeMaterialIcon';

interface ThemeToggleProps {
  size?: number;
}

export function ThemeToggle({ size = 24 }: ThemeToggleProps) {
  const { resolvedTheme, toggleTheme } = useTheme();
  const colors = Colors[resolvedTheme];

  const getThemeIcon = () => {
    return resolvedTheme === 'dark' ? 'wb-sunny' : 'nights-stay';
  };

  return (
    <TouchableOpacity
      style={[styles.toggleButton, { backgroundColor: colors.surface }]}
      onPress={toggleTheme}
      activeOpacity={0.7}
    >
      <SafeMaterialIcon 
        name={getThemeIcon()} 
        size={size} 
        color={colors.primary} 
        fallbackIcon={resolvedTheme === 'dark' ? 'sun' : 'moon'}
      />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  toggleButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.1)',
  },
});
