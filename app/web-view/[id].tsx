import React, { useState, useRef } from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Share,
  Animated,
  PanResponder,
  Dimensions,
} from 'react-native';
import { WebView } from 'react-native-webview';
import { useLocalSearchParams, router } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { MaterialIcons } from '@expo/vector-icons';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';

export default function WebViewScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const insets = useSafeAreaInsets();
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const [canGoBack, setCanGoBack] = useState(false);
  const [canGoForward, setCanGoForward] = useState(false);

  // Animation values for drag-to-close
  const translateY = useRef(new Animated.Value(0)).current;
  const { height } = Dimensions.get('window');
  const DRAG_THRESHOLD = height * 0.25; // 25% of screen height to trigger close

  // Pan responder for drag-to-close gesture
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

  if (!id) {
    router.back();
    return null;
  }

  const url = decodeURIComponent(id);
  const webViewRef = React.useRef<WebView>(null);

  const handleShare = React.useCallback(async () => {
    try {
      await Share.share({
        message: url,
        url: url,
      });
    } catch (error) {
      console.error('Error sharing article:', error);
    }
  }, [url]);

  const handleGoBack = React.useCallback(() => {
    if (canGoBack) {
      // Go back in WebView history
      webViewRef.current?.goBack();
    } else {
      // Go back to previous screen
      router.back();
    }
  }, [canGoBack]);

  const handleGoForward = React.useCallback(() => {
    if (canGoForward) {
      webViewRef.current?.goForward();
    }
  }, [canGoForward]);

  const handleRefresh = React.useCallback(() => {
    webViewRef.current?.reload();
  }, []);

  const handleNavigationStateChange = React.useCallback((navState: any) => {
    setCanGoBack(navState.canGoBack);
    setCanGoForward(navState.canGoForward);
  }, []);

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
      
      {/* Header Bar */}
      <View 
        style={[
          styles.header, 
          { 
            backgroundColor: colors.surface,
            paddingTop: insets.top + 8,
            borderBottomColor: colors.cardBorder,
          }
        ]}
      >
        <TouchableOpacity onPress={handleGoBack} style={styles.headerButton}>
          <MaterialIcons 
            name={canGoBack ? "arrow-back" : "close"} 
            size={24} 
            color={colors.text} 
          />
        </TouchableOpacity>

        <View style={styles.headerActions}>
          <TouchableOpacity 
            onPress={handleGoForward} 
            style={[styles.headerButton, { opacity: canGoForward ? 1 : 0.5 }]}
            disabled={!canGoForward}
          >
            <MaterialIcons name="arrow-forward" size={24} color={colors.text} />
          </TouchableOpacity>

          <TouchableOpacity onPress={handleRefresh} style={styles.headerButton}>
            <MaterialIcons name="refresh" size={24} color={colors.text} />
          </TouchableOpacity>

          <TouchableOpacity onPress={handleShare} style={styles.headerButton}>
            <MaterialIcons name="share" size={24} color={colors.text} />
          </TouchableOpacity>
        </View>
      </View>

      {/* WebView - Optimized for speed with no loading animation */}
      <WebView
        ref={webViewRef}
        source={{ uri: url }}
        style={[styles.webview, { backgroundColor: colors.background }]}
        onNavigationStateChange={handleNavigationStateChange}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        startInLoadingState={false} // Disable built-in loading for faster start
        scalesPageToFit={true}
        originWhitelist={['*']}
        mixedContentMode="always"
        cacheEnabled={true} // Enable caching for faster subsequent loads
        incognito={false} // Allow caching
        allowsBackForwardNavigationGestures={true} // Native gestures
        decelerationRate={0.998} // Normal deceleration (numeric value)
        bounces={false}
        scrollEnabled={true}
        showsHorizontalScrollIndicator={false}
        showsVerticalScrollIndicator={true}
        userAgent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
      />
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  dragIndicator: {
    width: 40,
    height: 4,
    borderRadius: 2,
    alignSelf: 'center',
    marginTop: 8,
    marginBottom: 8,
    opacity: 0.3,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingBottom: 8,
    borderBottomWidth: 1,
  },
  headerButton: {
    padding: 8,
    borderRadius: 20,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  loadingContainer: {
    position: 'absolute',
    top: 80, // Position below header
    left: 0,
    right: 0,
    height: 60, // Smaller loading area
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
    borderRadius: 8,
    marginHorizontal: 16,
  },
  webview: {
    flex: 1,
  },
});
