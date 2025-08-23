import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Share,
  Modal,
  Animated,
  Dimensions,
} from 'react-native';
import { WebView } from 'react-native-webview';
import { PanGestureHandler, State, GestureHandlerRootView } from 'react-native-gesture-handler';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { MaterialIcons } from '@expo/vector-icons';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';
import { BlurView } from 'expo-blur';

const { height: screenHeight } = Dimensions.get('window');

interface AnimatedWebViewModalProps {
  visible: boolean;
  url: string;
  onClose: () => void;
}

export const AnimatedWebViewModal: React.FC<AnimatedWebViewModalProps> = ({
  visible,
  url,
  onClose,
}) => {
  const insets = useSafeAreaInsets();
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const [canGoBack, setCanGoBack] = useState(false);
  const [canGoForward, setCanGoForward] = useState(false);

  const webViewRef = useRef<WebView>(null);
  const slideAnim = useRef(new Animated.Value(visible ? 0 : screenHeight)).current;
  const opacityAnim = useRef(new Animated.Value(visible ? 1 : 0)).current;
  const gestureRef = useRef(null);
  const dragTranslateY = useRef(new Animated.Value(0)).current;

  // Simple effect to handle animations without complex state management
  useEffect(() => {
    if (visible) {
      Animated.parallel([
        Animated.spring(slideAnim, {
          toValue: 0,
          useNativeDriver: true,
          tension: 100,
          friction: 8,
        }),
        Animated.timing(opacityAnim, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.spring(slideAnim, {
          toValue: screenHeight,
          useNativeDriver: true,
          tension: 100,
          friction: 8,
        }),
        Animated.timing(opacityAnim, {
          toValue: 0,
          duration: 250,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [visible, slideAnim, opacityAnim]);

  const handleClose = () => {
    onClose();
  };

  const onGestureEvent = Animated.event(
    [{ nativeEvent: { translationY: dragTranslateY } }],
    { useNativeDriver: true }
  );

  const onHandlerStateChange = (event: any) => {
    if (event.nativeEvent.oldState === State.ACTIVE) {
      const { translationY, velocityY } = event.nativeEvent;
      
      if (translationY > 150 || velocityY > 1000) {
        handleClose();
      } else {
        Animated.spring(dragTranslateY, {
          toValue: 0,
          useNativeDriver: true,
          tension: 100,
          friction: 8,
        }).start();
      }
    }
  };

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
      webViewRef.current?.goBack();
    } else {
      handleClose();
    }
  }, [canGoBack, handleClose]);

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
    <Modal
      visible={visible}
      transparent={true}
      animationType="none"
      onRequestClose={handleClose}
    >
      <GestureHandlerRootView style={{ flex: 1 }}>
        {/* Backdrop with blur effect */}
        <Animated.View
          style={[
            styles.backdrop,
            {
              opacity: opacityAnim,
            },
          ]}
        >
          <BlurView intensity={20} style={StyleSheet.absoluteFill} />
          <TouchableOpacity
            style={StyleSheet.absoluteFill}
            activeOpacity={1}
            onPress={handleClose}
          />
        </Animated.View>

        {/* Animated Modal Content */}
        <Animated.View
          style={[
            styles.modalContainer,
            {
              backgroundColor: colors.surface,
              transform: [
                { translateY: slideAnim },
                { translateY: dragTranslateY }
              ],
              paddingTop: insets.top + 10,
              paddingBottom: insets.bottom,
            },
          ]}
        >
          {/* Header with pull indicator - Only this area responds to gestures */}
          <PanGestureHandler
            ref={gestureRef}
            onGestureEvent={onGestureEvent}
            onHandlerStateChange={onHandlerStateChange}
          >
            <Animated.View style={styles.headerContainer}>
              <View style={[styles.pullIndicator, { backgroundColor: colors.outline }]} />
              
              <View style={[styles.header, { 
                borderBottomColor: colors.outline,
                backgroundColor: colors.surface,
              }]}>
                <TouchableOpacity 
                  onPress={handleGoBack} 
                  style={[styles.headerButton, { backgroundColor: colors.surfaceVariant }]}
                >
                  <MaterialIcons 
                    name={canGoBack ? "arrow-back" : "close"} 
                    size={24} 
                    color={colors.onSurface} 
                  />
                </TouchableOpacity>

                <View style={styles.headerActions}>
                  <TouchableOpacity 
                    onPress={handleGoForward} 
                    style={[
                      styles.headerButton, 
                      { 
                        backgroundColor: colors.surfaceVariant,
                        opacity: canGoForward ? 1 : 0.5 
                      }
                    ]}
                    disabled={!canGoForward}
                  >
                    <MaterialIcons name="arrow-forward" size={22} color={colors.onSurface} />
                  </TouchableOpacity>

                  <TouchableOpacity 
                    onPress={handleRefresh} 
                    style={[styles.headerButton, { backgroundColor: colors.surfaceVariant }]}
                  >
                    <MaterialIcons name="refresh" size={22} color={colors.onSurface} />
                  </TouchableOpacity>

                  <TouchableOpacity 
                    onPress={handleShare} 
                    style={[styles.headerButton, { backgroundColor: colors.primary }]}
                  >
                    <MaterialIcons name="share" size={22} color={colors.onPrimary} />
                  </TouchableOpacity>
                </View>
              </View>
            </Animated.View>
          </PanGestureHandler>

          {/* No more loading overlay - instant content display */}

          {/* WebView - No gesture handler, free scrolling, instant loading */}
          <WebView
            ref={webViewRef}
            source={{ uri: url }}
            style={[styles.webview, { backgroundColor: colors.background }]}
            onNavigationStateChange={handleNavigationStateChange}
            javaScriptEnabled={true}
            domStorageEnabled={true}
            startInLoadingState={false}
            scalesPageToFit={true}
            originWhitelist={['*']}
            mixedContentMode="always"
            cacheEnabled={true}
            incognito={false}
            allowsBackForwardNavigationGestures={true}
            decelerationRate={0.998}
            bounces={true}
            scrollEnabled={true}
            showsHorizontalScrollIndicator={false}
            showsVerticalScrollIndicator={true}
            userAgent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
          />
        </Animated.View>
      </GestureHandlerRootView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
  },
  modalContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: screenHeight * 0.95, // 95% of screen height for minimal gap
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: -8,
    },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 16,
    overflow: 'hidden',
  },
  headerContainer: {
    alignItems: 'center',
    paddingTop: 8,
  },
  pullIndicator: {
    width: 36,
    height: 4,
    borderRadius: 2,
    marginVertical: 8,
    opacity: 0.4,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    width: '100%',
  },
  headerButton: {
    padding: 12,
    borderRadius: 24,
    backgroundColor: 'rgba(0,0,0,0.04)',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  webview: {
    flex: 1,
    backgroundColor: 'transparent',
  },
});
