import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Image,
} from 'react-native';
import { useTheme } from '../store/ThemeContext';
import { useNews } from '../hooks/useNews';
import { Colors } from '../constants/Colors';
import { Typography } from '../constants/Typography';
import { sources } from '../services/api';

export function SourceGrid() {
  const { theme } = useTheme();
  const colors = Colors[theme];
  const { setSource, currentSource } = useNews();

  return (
    <View style={styles.grid}>
      {sources.map((source) => (
        <TouchableOpacity
          key={source.id}
          style={[
            styles.sourceCard,
            {
              backgroundColor: colors.card,
              borderColor: currentSource === source.id ? colors.primary : 'transparent',
            },
          ]}
          onPress={() => setSource(source.id)}
        >
          <Image source={{ uri: source.pic }} style={styles.sourceImage} />
          <Text
            style={[
              styles.sourceName,
              {
                color: currentSource === source.id ? colors.primary : colors.text,
              },
            ]}
          >
            {source.name}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    gap: 16,
  },
  sourceCard: {
    width: '47%',
    aspectRatio: 1.2,
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
  sourceImage: {
    width: 60,
    height: 60,
    marginBottom: 12,
    resizeMode: 'contain',
    borderRadius: 8,
  },
  sourceName: {
    ...Typography.caption,
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
});
