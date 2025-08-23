import React from 'react';
import { View, StyleSheet } from 'react-native';
import { useTheme } from '../store/ThemeContext';
import { Colors } from '../constants/Colors';

interface ScreenWrapperProps {
  children: React.ReactNode;
}

export const ScreenWrapper: React.FC<ScreenWrapperProps> = ({ children }) => {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme] || Colors.dark;

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
