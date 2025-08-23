import React, { useCallback, useRef, useState, useEffect } from 'react';
import {
  View,
  Dimensions,
  StyleSheet,
  Animated,
  PanResponder,
  StatusBar,
} from 'react-native';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';
import type { Article } from '../../types/news';
import { ModernArticleViewScreen } from './ModernArticleViewScreen';

interface VerticalArticleSwiperProps {
  articles: Article[];
  initialIndex?: number;
  onClose: () => void;
}

export function VerticalArticleSwiper({ articles, initialIndex = 0, onClose }: VerticalArticleSwiperProps) {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const { height, width } = Dimensions.get('window');
  
  const [currentIndex, setCurrentIndex] = useState(Math.max(0, Math.min(initialIndex, articles.length - 1)));
  const translateY = useRef(new Animated.Value(0)).current;
  const opacity = useRef(new Animated.Value(1)).current;
  const nextOpacity = useRef(new Animated.Value(0)).current;

  // Threshold for triggering swipe (30% of screen height)
  const SWIPE_THRESHOLD = height * 0.3;
  const VELOCITY_THRESHOLD = 0.8;

  // Pan responder for vertical swiping
  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, gestureState) => {
        // Respond to vertical swipes that are dominant over horizontal
        const isDominantlyVertical = Math.abs(gestureState.dy) > Math.abs(gestureState.dx) * 1.5;
        return isDominantlyVertical && Math.abs(gestureState.dy) > 10;
      },
      onPanResponderGrant: () => {
        translateY.setOffset((translateY as any)._value);
        translateY.setValue(0);
      },
      onPanResponderMove: (_, gestureState) => {
        const { dy } = gestureState;
        translateY.setValue(dy);
        
        // Create fade effect based on swipe distance
        const progress = Math.abs(dy) / SWIPE_THRESHOLD;
        const clampedProgress = Math.min(progress, 1);
        
        opacity.setValue(1 - clampedProgress * 0.7); // Current article fades out
        nextOpacity.setValue(clampedProgress * 0.3); // Next article fades in slightly
      },
      onPanResponderRelease: (_, gestureState) => {
        const { dy, vy } = gestureState;
        translateY.flattenOffset();
        
        const shouldSwipe = Math.abs(dy) > SWIPE_THRESHOLD || Math.abs(vy) > VELOCITY_THRESHOLD;
        
        if (shouldSwipe) {
          // Determine direction
          const isSwipingUp = dy < 0;
          const isSwipingDown = dy > 0;
          
          if (isSwipingUp && currentIndex < articles.length - 1) {
            // Swipe to next article (up)
            animateToNext(1);
          } else if (isSwipingDown && currentIndex > 0) {
            // Swipe to previous article (down)
            animateToNext(-1);
          } else if (isSwipingDown && currentIndex === 0) {
            // Close if swiping down on first article
            animateClose();
          } else {
            // Snap back
            animateSnapBack();
          }
        } else {
          // Snap back
          animateSnapBack();
        }
      },
    })
  ).current;

  const animateToNext = (direction: number) => {
    const targetY = direction > 0 ? -height : height;
    
    // Animate current article out
    Animated.parallel([
      Animated.timing(translateY, {
        toValue: targetY,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(opacity, {
        toValue: 0,
        duration: 250,
        useNativeDriver: true,
      }),
    ]).start(() => {
      // Update index
      const newIndex = currentIndex + direction;
      setCurrentIndex(newIndex);
      
      // Reset position and fade in new article
      translateY.setValue(0);
      opacity.setValue(0);
      nextOpacity.setValue(0);
      
      Animated.timing(opacity, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }).start();
    });
  };

  const animateSnapBack = () => {
    Animated.parallel([
      Animated.spring(translateY, {
        toValue: 0,
        tension: 100,
        friction: 8,
        useNativeDriver: true,
      }),
      Animated.timing(opacity, {
        toValue: 1,
        duration: 200,
        useNativeDriver: true,
      }),
      Animated.timing(nextOpacity, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const animateClose = () => {
    Animated.parallel([
      Animated.timing(translateY, {
        toValue: height,
        duration: 300,
        useNativeDriver: true,
      }),
      Animated.timing(opacity, {
        toValue: 0,
        duration: 200,
        useNativeDriver: true,
      }),
    ]).start(() => {
      onClose();
    });
  };

  const currentArticle = articles[currentIndex];
  const nextArticle = articles[currentIndex + 1];
  const prevArticle = articles[currentIndex - 1];

  return (
    <View style={styles.container}>
      <StatusBar hidden />
      
      {/* Main Article */}
      <Animated.View
        style={[
          styles.articleContainer,
          {
            transform: [{ translateY }],
            opacity,
          },
        ]}
        {...panResponder.panHandlers}
      >
        <ModernArticleViewScreen
          article={currentArticle}
          onBack={onClose}
        />
      </Animated.View>

      {/* Progress Indicator */}
      <View style={styles.progressContainer}>
        {articles.map((_, index) => (
          <View
            key={index}
            style={[
              styles.progressDot,
              {
                backgroundColor: index === currentIndex ? colors.primary : colors.textSecondary,
                opacity: index === currentIndex ? 1 : 0.3,
              },
            ]}
          />
        ))}
      </View>

      {/* Swipe Indicators */}
      <View style={styles.indicatorContainer}>
        {currentIndex > 0 && (
          <View style={[styles.swipeIndicator, styles.topIndicator]}>
            <View style={[styles.indicatorLine, { backgroundColor: colors.textSecondary }]} />
          </View>
        )}
        {currentIndex < articles.length - 1 && (
          <View style={[styles.swipeIndicator, styles.bottomIndicator]}>
            <View style={[styles.indicatorLine, { backgroundColor: colors.textSecondary }]} />
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  articleContainer: {
    flex: 1,
    width: '100%',
    height: '100%',
  },
  progressContainer: {
    position: 'absolute',
    top: 50,
    right: 20,
    flexDirection: 'column',
    alignItems: 'center',
    zIndex: 1000,
  },
  progressDot: {
    width: 4,
    height: 12,
    borderRadius: 2,
    marginVertical: 2,
  },
  indicatorContainer: {
    position: 'absolute',
    left: 20,
    top: 0,
    bottom: 0,
    width: 3,
    justifyContent: 'center',
    zIndex: 1000,
  },
  swipeIndicator: {
    position: 'absolute',
    left: 0,
    width: 3,
    height: 60,
    justifyContent: 'center',
    alignItems: 'center',
  },
  topIndicator: {
    top: '40%',
  },
  bottomIndicator: {
    bottom: '40%',
  },
  indicatorLine: {
    width: 2,
    height: 30,
    borderRadius: 1,
    opacity: 0.5,
  },
});
