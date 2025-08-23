import { useRef } from 'react';
import { Animated, PanResponder, Dimensions } from 'react-native';
import { router } from 'expo-router';

/**
 * Custom hook for drag-to-close functionality
 * Provides smooth drag down gesture to close screens
 */
export const useDragToClose = () => {
  const translateY = useRef(new Animated.Value(0)).current;
  const { height } = Dimensions.get('window');
  const DRAG_THRESHOLD = height * 0.25; // 25% of screen height to trigger close

  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (evt, gestureState) => {
        // Only respond to vertical drags starting from the top area
        return Math.abs(gestureState.dy) > Math.abs(gestureState.dx) && 
               gestureState.dy > 0 && 
               evt.nativeEvent.pageY < 150; // Only trigger from top 150px
      },
      onPanResponderGrant: () => {
        translateY.setOffset((translateY as any)._value);
        translateY.setValue(0);
      },
      onPanResponderMove: (_, gestureState) => {
        // Only allow downward drag
        if (gestureState.dy >= 0) {
          translateY.setValue(gestureState.dy);
        }
      },
      onPanResponderRelease: (_, gestureState) => {
        translateY.flattenOffset();
        
        if (gestureState.dy > DRAG_THRESHOLD || gestureState.vy > 1.5) {
          // Close the view with animation
          Animated.timing(translateY, {
            toValue: height,
            duration: 300,
            useNativeDriver: true,
          }).start(() => {
            router.back();
          });
        } else {
          // Snap back to original position
          Animated.spring(translateY, {
            toValue: 0,
            tension: 100,
            friction: 8,
            useNativeDriver: true,
          }).start();
        }
      },
    })
  ).current;

  return {
    translateY,
    panHandlers: panResponder.panHandlers,
  };
};
