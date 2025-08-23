import { useLocalSearchParams, router } from 'expo-router';
import { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Animated,
  PanResponder,
  Dimensions,
} from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';
import { InstantView } from '../../components/ui/InstantView';
import type { Article } from '../../types/news';

export default function InstantViewScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { theme } = useTheme();
  const colors = Colors[theme === 'auto' ? 'light' : theme];
  const [article, setArticle] = useState<Article | null>(null);
  const [loading, setLoading] = useState(true);

  // Animation values for drag-to-close
  const translateY = useRef(new Animated.Value(0)).current;
  const { height } = Dimensions.get('window');
  const DRAG_THRESHOLD = height * 0.25; // 25% of screen height to trigger close

  // Pan responder for drag-to-close gesture
  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (evt, gestureState) => {
        return Math.abs(gestureState.dy) > Math.abs(gestureState.dx) && 
               gestureState.dy > 0 && 
               evt.nativeEvent.pageY < 150;
      },
      onPanResponderGrant: () => {
        translateY.setOffset((translateY as any)._value);
        translateY.setValue(0);
      },
      onPanResponderMove: (_, gestureState) => {
        if (gestureState.dy >= 0) {
          translateY.setValue(gestureState.dy);
        }
      },
      onPanResponderRelease: (_, gestureState) => {
        translateY.flattenOffset();
        
        if (gestureState.dy > DRAG_THRESHOLD || gestureState.vy > 1.5) {
          Animated.timing(translateY, {
            toValue: height,
            duration: 300,
            useNativeDriver: true,
          }).start(() => {
            router.back();
          });
        } else {
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

  useEffect(() => {
    if (id) {
      const decodedUrl = decodeURIComponent(id);
      // Create a minimal article object for the WebView
      const webViewArticle: Article = {
        url: decodedUrl,
        title: 'Loading...',
        description: null,
        summary: null,
        source: { id: null, name: 'Original Source' },
        author: null,
        urlToImage: null,
        publishedAt: new Date().toISOString(),
        content: null
      };
      setArticle(webViewArticle);
      setLoading(false);
    }
  }, [id]);

  if (loading) {
    return (
      <View style={[styles.container, styles.centered, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
          Loading article...
        </Text>
      </View>
    );
  }

  if (!article) {
    return (
      <View style={[styles.container, styles.centered, { backgroundColor: colors.background }]}>
        <MaterialIcons name="article" size={64} color={colors.textSecondary} />
        <Text style={[styles.errorText, { color: colors.textSecondary }]}>
          Article not found
        </Text>
        <TouchableOpacity
          style={[styles.button, { backgroundColor: colors.primary }]}
          onPress={() => router.back()}
        >
          <Text style={[styles.buttonText, { color: colors.background }]}>
            Go Back
          </Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <Animated.View 
      style={[
        { 
          flex: 1,
          backgroundColor: colors.background,
          transform: [{ translateY }]
        }
      ]}
      {...panResponder.panHandlers}
    >
      {/* Drag Indicator */}
      <View style={[styles.dragIndicator, { backgroundColor: colors.textSecondary }]} />
      
      <InstantView
        article={article}
        onBack={() => router.back()}
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
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    ...Typography.bodyMedium,
    fontSize: 16,
    marginTop: 16,
  },
  errorText: {
    ...Typography.bodyMedium,
    fontSize: 16,
    marginTop: 16,
    marginBottom: 24,
    textAlign: 'center',
  },
  button: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  buttonText: {
    ...Typography.labelLarge,
    fontSize: 16,
    fontWeight: '600',
  },
});
