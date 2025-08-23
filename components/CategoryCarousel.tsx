import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Image,
} from 'react-native';
import { useTheme } from '../store/ThemeContext';
import { useNews } from '../hooks/useNews';
import { Colors } from '../constants/Colors';
import { Typography } from '../constants/Typography';
import { categories } from '../services/api';

export function CategoryCarousel() {
  const { theme } = useTheme();
  const colors = Colors[theme];
  const { setCategory, currentCategory } = useNews();

  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.container}
    >
      {categories.map((category, index) => (
        <TouchableOpacity
          key={category.name}
          style={[
            styles.categoryCard,
            {
              backgroundColor: colors.card,
              borderColor: currentCategory === category.name ? colors.primary : 'transparent',
            },
          ]}
          onPress={() => setCategory(category.name)}
        >
          <Image source={{ uri: category.pic }} style={styles.categoryImage} />
          <Text
            style={[
              styles.categoryName,
              {
                color: currentCategory === category.name ? colors.primary : colors.text,
              },
            ]}
          >
            {category.name}
          </Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 4,
    paddingVertical: 8,
  },
  categoryCard: {
    width: 120,
    height: 120,
    marginHorizontal: 8,
    borderRadius: 16,
    padding: 16,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  categoryImage: {
    width: 48,
    height: 48,
    marginBottom: 12,
    resizeMode: 'contain',
  },
  categoryName: {
    ...Typography.caption,
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
    textTransform: 'capitalize',
  },
});
