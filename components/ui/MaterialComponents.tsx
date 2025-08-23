import React from 'react';
import { View, ViewStyle, StyleProp, Pressable } from 'react-native';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';

export interface MaterialCardProps {
  children: React.ReactNode;
  variant?: 'elevated' | 'filled' | 'outlined';
  style?: StyleProp<ViewStyle>;
  onPress?: () => void;
}

export function MaterialCard({ 
  children, 
  variant = 'elevated', 
  style,
  onPress 
}: MaterialCardProps) {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];

  const getCardStyle = (): ViewStyle => {
    const baseStyle: ViewStyle = {
      borderRadius: 12,
      padding: 16,
    };

    switch (variant) {
      case 'elevated':
        return {
          ...baseStyle,
          backgroundColor: colors.card,
          shadowColor: colors.shadow,
          shadowOffset: {
            width: 0,
            height: 2,
          },
          shadowOpacity: 0.1,
          shadowRadius: 8,
          elevation: 3,
        };
      case 'filled':
        return {
          ...baseStyle,
          backgroundColor: colors.surfaceContainer,
        };
      case 'outlined':
        return {
          ...baseStyle,
          backgroundColor: colors.surface,
          borderWidth: 1,
          borderColor: colors.outline,
        };
      default:
        return baseStyle;
    }
  };

  if (onPress) {
    return (
      <Pressable style={[getCardStyle(), style]} onPress={onPress}>
        {children}
      </Pressable>
    );
  }
  
  return (
    <View style={[getCardStyle(), style]}>
      {children}
    </View>
  );
}

export interface MaterialDividerProps {
  inset?: number;
  style?: StyleProp<ViewStyle>;
}

export function MaterialDivider({ inset = 0, style }: MaterialDividerProps) {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];

  return (
    <View
      style={[
        {
          height: 1,
          backgroundColor: colors.outline,
          marginLeft: inset,
        },
        style,
      ]}
    />
  );
}

export interface MaterialElevationProps {
  level: 0 | 1 | 2 | 3 | 4 | 5;
  children: React.ReactNode;
  style?: StyleProp<ViewStyle>;
}

export function MaterialElevation({ level, children, style }: MaterialElevationProps) {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];

  const getElevationStyle = (): ViewStyle => {
    const elevationStyles: Record<number, ViewStyle> = {
      0: {
        backgroundColor: colors.elevation.level0,
      },
      1: {
        backgroundColor: colors.elevation.level1,
        shadowColor: colors.shadow,
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 2,
        elevation: 1,
      },
      2: {
        backgroundColor: colors.elevation.level2,
        shadowColor: colors.shadow,
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.08,
        shadowRadius: 4,
        elevation: 2,
      },
      3: {
        backgroundColor: colors.elevation.level3,
        shadowColor: colors.shadow,
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.12,
        shadowRadius: 8,
        elevation: 3,
      },
      4: {
        backgroundColor: colors.elevation.level4,
        shadowColor: colors.shadow,
        shadowOffset: { width: 0, height: 8 },
        shadowOpacity: 0.16,
        shadowRadius: 12,
        elevation: 4,
      },
      5: {
        backgroundColor: colors.elevation.level5,
        shadowColor: colors.shadow,
        shadowOffset: { width: 0, height: 12 },
        shadowOpacity: 0.20,
        shadowRadius: 16,
        elevation: 5,
      },
    };

    return elevationStyles[level] || elevationStyles[0];
  };

  return (
    <View style={[getElevationStyle(), style]}>
      {children}
    </View>
  );
}
