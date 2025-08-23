"use client"

import type React from "react"
import { useState, useRef } from "react"
import { View, StyleSheet, TouchableOpacity, Share, Modal, Dimensions, Text } from "react-native"
import { WebView } from "react-native-webview"
import { useSafeAreaInsets } from "react-native-safe-area-context"
import { MaterialIcons } from "@expo/vector-icons"
import { useTheme } from "../../store/ThemeContext"
import { Colors } from "../../constants/Colors"
import { BlurView } from "expo-blur"
import { PanGestureHandler } from "react-native-gesture-handler"
import Animated, {
  useSharedValue,
  useAnimatedGestureHandler,
  useAnimatedStyle,
  withSpring,
  withTiming,
  runOnJS,
  interpolate,
  Extrapolate,
} from "react-native-reanimated"

const { height: screenHeight } = Dimensions.get("window")

interface SimpleWebViewModalProps {
  visible: boolean
  url: string
  onClose: () => void
}

export const SimpleWebViewModal: React.FC<SimpleWebViewModalProps> = ({ visible, url, onClose }) => {
  const insets = useSafeAreaInsets()
  const { resolvedTheme } = useTheme()
  const colors = Colors[resolvedTheme]
  const [canGoBack, setCanGoBack] = useState(false)
  const [loading, setLoading] = useState(true)

  const webViewRef = useRef<WebView>(null)

  // Animation values for drag-to-close
  const translateY = useSharedValue(0)
  const opacity = useSharedValue(1)

  // Gesture handler for pull-down to close
  const gestureHandler = useAnimatedGestureHandler({
    onStart: (_, context: any) => {
      context.startY = translateY.value
    },
    onActive: (event, context: any) => {
      const newY = Math.max(0, context.startY + event.translationY)
      translateY.value = newY

      // Fade out as user drags down
      const progress = newY / (screenHeight * 0.3)
      opacity.value = interpolate(progress, [0, 1], [1, 0.7], Extrapolate.CLAMP)
    },
    onEnd: (event) => {
      const shouldClose = event.translationY > 150 || event.velocityY > 1000

      if (shouldClose) {
        // Animate out and close
        translateY.value = withTiming(screenHeight, { duration: 300 })
        opacity.value = withTiming(0, { duration: 300 })
        runOnJS(onClose)()
      } else {
        // Snap back to original position
        translateY.value = withSpring(0, {
          damping: 20,
          stiffness: 300,
        })
        opacity.value = withSpring(1)
      }
    },
  })

  // Animated styles
  const animatedModalStyle = useAnimatedStyle(() => {
    return {
      transform: [{ translateY: translateY.value }],
      opacity: opacity.value,
    }
  })

  const animatedBackdropStyle = useAnimatedStyle(() => {
    const backdropOpacity = interpolate(translateY.value, [0, screenHeight * 0.3], [0.6, 0.2], Extrapolate.CLAMP)
    return {
      opacity: backdropOpacity,
    }
  })

  const handleShare = async () => {
    try {
      await Share.share({
        message: url,
        url: url,
      })
    } catch (error) {
      console.error("Error sharing article:", error)
    }
  }

  const handleGoBack = () => {
    if (canGoBack) {
      webViewRef.current?.goBack()
    } else {
      onClose()
    }
  }

  const handleRefresh = () => {
    webViewRef.current?.reload()
  }

  const handleNavigationStateChange = (navState: any) => {
    setCanGoBack(navState.canGoBack)
    setLoading(navState.loading)
  }

  if (!visible) {
    return null
  }

  return (
    <Modal
      visible={visible}
      transparent={true}
      animationType="fade"
      onRequestClose={onClose}
      presentationStyle="overFullScreen"
    >
      {/* Backdrop with blur effect */}
      <Animated.View style={[styles.backdrop, animatedBackdropStyle]}>
        <BlurView intensity={20} style={StyleSheet.absoluteFill} />
        <TouchableOpacity style={StyleSheet.absoluteFill} activeOpacity={1} onPress={onClose} />
      </Animated.View>

      {/* Modal Content with PanGestureHandler */}
      <PanGestureHandler onGestureEvent={gestureHandler}>
        <Animated.View
          style={[
            styles.modalContainer,
            {
              backgroundColor: colors.surface,
              paddingTop: insets.top + 4, // Reduced from 10 to 4
            },
            animatedModalStyle,
          ]}
        >
          {/* Compact Header */}
          <View style={styles.headerContainer}>
            <View style={[styles.pullIndicator, { backgroundColor: colors.outline }]} />
            <View
              style={[
                styles.header,
                {
                  borderBottomColor: colors.outline + "40",
                  backgroundColor: colors.surface,
                },
              ]}
            >
              <TouchableOpacity
                onPress={handleGoBack}
                style={[styles.headerButton, { backgroundColor: colors.surfaceVariant }]}
              >
                <MaterialIcons
                  name={canGoBack ? "arrow-back" : "close"}
                  size={20} // Reduced from 22 to 20
                  color={colors.onSurface}
                />
              </TouchableOpacity>
              {loading && <Text style={[styles.loadingText, { color: colors.onSurface }]}>Loading...</Text>}
              <View style={styles.headerActions}>
                <TouchableOpacity
                  onPress={handleRefresh}
                  style={[styles.headerButton, { backgroundColor: colors.surfaceVariant }]}
                >
                  <MaterialIcons name="refresh" size={16} color={colors.onSurface} />
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={handleShare}
                  style={[styles.headerButton, { backgroundColor: colors.primary }]}
                >
                  <MaterialIcons name="share" size={16} color={colors.onPrimary} />
                </TouchableOpacity>
              </View>
            </View>
          </View>

          {/* WebView - More space for content */}
          <WebView
            ref={webViewRef}
            source={{ uri: url }}
            style={[styles.webview, { backgroundColor: colors.background }]}
            onNavigationStateChange={handleNavigationStateChange}
            javaScriptEnabled={true}
            domStorageEnabled={true}
            startInLoadingState={false}
            scalesPageToFit={true}
            originWhitelist={["*"]}
            mixedContentMode="always"
            cacheEnabled={true}
            incognito={false}
            allowsBackForwardNavigationGestures={true}
            decelerationRate={0.998}
            bounces={true}
            scrollEnabled={true}
            showsHorizontalScrollIndicator={false}
            showsVerticalScrollIndicator={false} // Removed scroll indicator for cleaner look
            userAgent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
          />
        </Animated.View>
      </PanGestureHandler>
    </Modal>
  )
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.6)",
  },
  modalContainer: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    height: screenHeight * 0.92, // Increased from 0.85 to 0.92 for more content space
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    shadowColor: "#000",
    shadowOffset: {
      width: 0,
      height: -8,
    },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 16,
    overflow: "hidden",
  },
  headerContainer: {
    alignItems: "center",
    paddingTop: 4, // Reduced from 8 to 4
  },
  pullIndicator: {
    width: 36,
    height: 4,
    borderRadius: 2,
    marginVertical: 4, // Reduced from 8 to 4
    opacity: 0.6, // Increased visibility for better UX
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 8, // Reduced from 12 to 8
    borderBottomWidth: 0.5, // Made thinner
    width: "100%",
  },
  headerButton: {
    padding: 6, // Reduced from 8 to 6
    borderRadius: 12, // Reduced from 16 to 12
  },
  headerActions: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6, // Reduced from 8 to 6
  },
  loadingText: {
    fontSize: 13, // Reduced from 14 to 13
    fontWeight: "500",
  },
  webview: {
    flex: 1,
    backgroundColor: "transparent",
  },
})
