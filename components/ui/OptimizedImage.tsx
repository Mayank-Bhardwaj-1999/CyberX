import React, { useState, useCallback } from 'react';
import { View, StyleSheet, Dimensions } from 'react-native';
import { Image } from 'expo-image';
import { MaterialIcons } from '@expo/vector-icons';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';

const { width } = Dimensions.get('window');

interface OptimizedImageProps {
  source: string | null;
  style?: any;
  aspectRatio?: number;
  borderRadius?: number;
  placeholder?: string;
}

export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  source,
  style,
  aspectRatio = 16 / 9,
  borderRadius = 12,
  placeholder = 'image'
}) => {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const [imageError, setImageError] = useState(false);

  const handleError = useCallback(() => {
    setImageError(true);
  }, []);

  const imageHeight = style?.height || (width - 32) / aspectRatio;

  // Use a valid Material icon for placeholder
  const getPlaceholderIcon = (placeholderValue: string) => {
    // Check if it's a valid Material icon name (simple check)
    if (placeholderValue.length > 20 || placeholderValue.includes('?') || placeholderValue.includes('%')) {
      return 'image'; // Default fallback icon
    }
    return placeholderValue;
  };

  if (!source || imageError) {
    return (
      <View style={[
        styles.placeholder,
        style,
        {
          backgroundColor: colors.surfaceVariant,
          height: imageHeight,
          borderRadius,
        }
      ]}>
        <MaterialIcons 
          name={getPlaceholderIcon(placeholder) as any} 
          size={24} 
          color={colors.onSurfaceVariant} 
        />
      </View>
    );
  }

  return (
    <Image
      source={{ uri: source }}
      style={[
        style,
        {
          height: imageHeight,
          borderRadius,
        }
      ]}
      contentFit="cover"
      transition={200}
      onError={handleError}
      cachePolicy="memory-disk"
      priority="high"
      placeholder={{
        blurhash: 'L6PZfSi_.AyE_3t7t7R**0o#DgR4',
      }}
      placeholderContentFit="cover"
    />
  );
};

const styles = StyleSheet.create({
  placeholder: {
    justifyContent: 'center',
    alignItems: 'center',
    opacity: 0.7,
  },
});
