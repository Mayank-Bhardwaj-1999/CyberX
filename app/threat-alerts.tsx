import { useEffect } from 'react';
import { router } from 'expo-router';
import { View, Text, StyleSheet } from 'react-native';
import { useTheme } from '../store/ThemeContext';
import { Colors } from '../constants/Colors';

export default function ThreatAlertsRedirect() {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];

  useEffect(() => {
    // Redirect back to main news screen since internal pages are removed for better UX
    const timer = setTimeout(() => {
      router.replace('/(tabs)/news');
    }, 100);

    return () => clearTimeout(timer);
  }, []);

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <Text style={[styles.text, { color: colors.text }]}>
        Redirecting to main news...
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  text: {
    fontSize: 16,
    textAlign: 'center',
  },
});
