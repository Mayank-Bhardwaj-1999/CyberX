import React from 'react';
import { View, Text, StyleSheet, ScrollView, Image } from 'react-native';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';

interface Block { type: 'text' | 'heading'; text: string; }
interface ArticleReaderProps {
  title: string;
  image?: string;
  domain?: string;
  blocks: Block[];
  wordCount: number;
}

export const ArticleReader: React.FC<ArticleReaderProps> = ({ title, image, domain, blocks, wordCount }) => {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];

  return (
    <ScrollView style={[styles.container,{ backgroundColor: colors.background }]} contentContainerStyle={styles.content}>
      <Text style={[styles.title,{ color: colors.text }]}>{title}</Text>
      {domain && <Text style={[styles.domain,{ color: colors.textSecondary }]}>Source: {domain}</Text>}
      {image ? (
        <Image source={{ uri: image }} style={styles.image} resizeMode="cover" />
      ) : null}
      <Text style={[styles.meta,{ color: colors.textSecondary }]}>Approx. {Math.max(1, Math.round(wordCount/220))} min read</Text>
      <View style={styles.divider} />
      {blocks.map((b, idx) => (
        <Text key={idx} style={b.type === 'heading' ? [styles.heading,{ color: colors.text }] : [styles.paragraph,{ color: colors.textSecondary }]}> 
          {b.text}
        </Text>
      ))}
      <View style={{ height: 48 }} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  content: { padding: 16 },
  title: { ...Typography.titleLarge, fontSize: 24, fontWeight: '700', marginBottom: 4 },
  domain: { ...Typography.caption, marginBottom: 8 },
  image: { width: '100%', height: 200, borderRadius: 12, marginBottom: 12 },
  meta: { ...Typography.caption, marginBottom: 12 },
  divider: { height: 1, backgroundColor: 'rgba(255,255,255,0.1)', marginBottom: 16 },
  heading: { ...Typography.titleMedium, fontSize: 18, fontWeight: '600', marginTop: 16, marginBottom: 8 },
  paragraph: { ...Typography.bodyMedium, fontSize: 16, lineHeight: 24, marginBottom: 12 }
});
