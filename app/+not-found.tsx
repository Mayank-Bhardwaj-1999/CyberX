import { Link, Stack } from 'expo-router';
import { StyleSheet, View, Text } from 'react-native';
import { useTheme } from '../store/ThemeContext';
import { Colors } from '../constants/Colors';
import { Typography } from '../constants/Typography';

export default function NotFoundScreen() {
  const { theme } = useTheme();
  const colors = Colors[theme as keyof typeof Colors];

  return (
    <>
      <Stack.Screen options={{ title: 'Oops!' }} />
      <View style={[styles.container, { backgroundColor: colors.background }]}>
        <Text style={[styles.title, { color: colors.text }]}>
          This screen doesn't exist.
        </Text>
        <Link href="/(tabs)/news" style={[styles.link, { color: colors.primary }]}>
          <Text>Go to News Screen!</Text>
        </Link>
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    ...Typography.title,
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  link: {
    ...Typography.body,
    fontSize: 16,
    textDecorationLine: 'underline',
  },
});
