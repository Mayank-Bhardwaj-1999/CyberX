import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated } from 'react-native';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';

interface LoadingSkeletonProps {
  width?: number | string;
  height?: number;
  borderRadius?: number;
  style?: any;
}

export function LoadingSkeleton({ 
  width = '100%', 
  height = 20, 
  borderRadius = 4,
  style 
}: LoadingSkeletonProps) {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const animatedValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(animatedValue, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: false,
        }),
        Animated.timing(animatedValue, {
          toValue: 0,
          duration: 1000,
          useNativeDriver: false,
        }),
      ])
    );
    animation.start();
    return () => animation.stop();
  }, [animatedValue]);

  const opacity = animatedValue.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 0.7],
  });

  return (
    <Animated.View
      style={[
        styles.skeleton,
        {
          width,
          height,
          borderRadius,
          backgroundColor: colors.cardBorder,
          opacity,
        },
        style,
      ]}
    />
  );
}

export function NewsCardSkeleton() {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];

  return (
    <View style={[styles.cardContainer, { backgroundColor: colors.surface }]}>
      {/* Image skeleton */}
      <LoadingSkeleton 
        width="100%" 
        height={180} 
        borderRadius={16}
        style={styles.imageSkeleton}
      />
      
      {/* Content skeleton */}
      <View style={styles.contentContainer}>
        {/* Title skeleton */}
        <LoadingSkeleton width="90%" height={16} style={styles.titleSkeleton} />
        <LoadingSkeleton width="70%" height={16} style={styles.titleSkeleton} />
        
        {/* Description skeleton */}
        <LoadingSkeleton width="100%" height={14} style={styles.descSkeleton} />
        <LoadingSkeleton width="80%" height={14} style={styles.descSkeleton} />
        
        {/* Metadata skeleton */}
        <View style={styles.metadataContainer}>
          <LoadingSkeleton width={80} height={12} />
          <View style={styles.actionSkeleton}>
            <LoadingSkeleton width={32} height={32} borderRadius={16} />
            <LoadingSkeleton width={32} height={32} borderRadius={16} />
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  skeleton: {
    backgroundColor: '#E2E8F0',
  },
  cardContainer: {
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 4,
  },
  imageSkeleton: {
    marginBottom: 0,
  },
  contentContainer: {
    padding: 16,
  },
  titleSkeleton: {
    marginBottom: 8,
  },
  descSkeleton: {
    marginBottom: 6,
  },
  metadataContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  actionSkeleton: {
    flexDirection: 'row',
    gap: 8,
  },
});
