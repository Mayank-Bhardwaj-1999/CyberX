import React, { useCallback, useMemo, useRef, useState } from 'react'
import { View, Dimensions, FlatList, StyleSheet, Animated, PanResponder } from 'react-native'
import { useTheme } from '../../store/ThemeContext'
import { Colors } from '../../constants/Colors'
import type { Article } from '../../types/news'
import { ModernArticleViewScreen } from './ModernArticleViewScreen'

interface ArticlePagerProps {
  articles: Article[]
  initialIndex?: number
  onClose: () => void
}

export function ArticlePager({ articles, initialIndex = 0, onClose }: ArticlePagerProps) {
  const { resolvedTheme } = useTheme()
  const colors = Colors[resolvedTheme]
  const { width, height } = Dimensions.get('window')
  const listRef = useRef<FlatList>(null)
  const [index, setIndex] = useState(Math.max(0, Math.min(initialIndex, Math.max(articles.length - 1, 0))))

  // Animation values for drag-to-close
  const translateY = useRef(new Animated.Value(0)).current
  const DRAG_THRESHOLD = height * 0.25

  // Pan responder for drag-to-close gesture (only vertical)
  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (evt, gestureState) => {
        // Only respond to vertical drags that are dominant over horizontal
        const isDominantlyVertical = Math.abs(gestureState.dy) > Math.abs(gestureState.dx) * 2
        const isDownward = gestureState.dy > 0
        const isFromTop = evt.nativeEvent.pageY < 150
        return isDominantlyVertical && isDownward && isFromTop
      },
      onPanResponderGrant: () => {
        translateY.setOffset((translateY as any)._value)
        translateY.setValue(0)
      },
      onPanResponderMove: (_, gestureState) => {
        if (gestureState.dy >= 0) {
          translateY.setValue(gestureState.dy)
        }
      },
      onPanResponderRelease: (_, gestureState) => {
        translateY.flattenOffset()
        
        if (gestureState.dy > DRAG_THRESHOLD || gestureState.vy > 1.5) {
          Animated.timing(translateY, {
            toValue: height,
            duration: 300,
            useNativeDriver: true,
          }).start(() => {
            onClose()
          })
        } else {
          Animated.spring(translateY, {
            toValue: 0,
            tension: 100,
            friction: 8,
            useNativeDriver: true,
          }).start()
        }
      },
    })
  ).current

  const keyExtractor = useCallback((item: Article, i: number) => `${item.url}-${i}` , [])

  const getItemLayout = useCallback((_: any, i: number) => ({ length: width, offset: width * i, index: i }), [width])

  const renderItem = useCallback(({ item }: { item: Article }) => (
    <View style={{ width }}>
      <ModernArticleViewScreen article={item} onBack={onClose} />
    </View>
  ), [onClose, width])

  const onMomentumScrollEnd = useCallback((ev: any) => {
    const newIndex = Math.round(ev.nativeEvent.contentOffset.x / width)
    if (!Number.isNaN(newIndex)) setIndex(newIndex)
  }, [width])

  return (
    <Animated.View 
      style={[
        styles.container,
        { 
          backgroundColor: colors.background,
          transform: [{ translateY }]
        }
      ]}
      {...panResponder.panHandlers}
    >
      {/* Drag Indicator */}
      <View style={[styles.dragIndicator, { backgroundColor: colors.textSecondary }]} />
      
      <FlatList
        ref={listRef}
        data={articles}
        keyExtractor={keyExtractor}
        renderItem={renderItem}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        initialScrollIndex={index}
        getItemLayout={getItemLayout}
        onMomentumScrollEnd={onMomentumScrollEnd}
        windowSize={3}
        maxToRenderPerBatch={2}
        removeClippedSubviews
      />
    </Animated.View>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  dragIndicator: {
    width: 40,
    height: 4,
    borderRadius: 2,
    alignSelf: 'center',
    marginTop: 8,
    marginBottom: 8,
    opacity: 0.3,
  },
})


