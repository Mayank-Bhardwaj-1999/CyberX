import React from 'react';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';
import { useWindowDimensions } from 'react-native';
import { EmptyState } from '../../components/ui/EmptyState';

export default function SavedScreen() {
  const insets = useSafeAreaInsets();
  const { width } = useWindowDimensions();
  const horizontalPad = width >= 900 ? 36 : width >= 600 ? 24 : 16;

  return (
    <SafeAreaView style={{ flex: 1, paddingTop: insets.top }} edges={['top', 'left', 'right', 'bottom']}>
      <EmptyState
        title="No bookmarks yet"
        subtitle="Save articles to read them later"
        icon="bookmark"
        // EmptyState already applies bottom inset; pass no extra wrapper padding needed
      />
    </SafeAreaView>
  );
}