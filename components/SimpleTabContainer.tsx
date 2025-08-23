import React from 'react';
import { View, StyleSheet } from 'react-native';

interface SwipeableTabContainerProps {
  children: React.ReactNode;
}

export const SwipeableTabContainer: React.FC<SwipeableTabContainerProps> = ({ children }) => {
  return (
    <View style={styles.container}>
      {children}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
