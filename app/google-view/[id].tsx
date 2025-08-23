import { useLocalSearchParams, router } from 'expo-router';
import { useEffect, useState, useRef } from 'react';
import { 
  View, 
  ActivityIndicator, 
  Text, 
  StyleSheet,
  Animated,
  PanResponder,
  Dimensions,
} from 'react-native';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';
import { InstantView } from '../../components/ui/InstantView';
import type { Article } from '../../types/news';
import { generateConsistentRiskScore, getThreatLevel } from '../../utils/threatAnalysis';
import { getTempArticle } from '../../utils/tempArticleStore';

// Screen to display a Google News sourced article inside the app using InstantView
export default function GoogleArticleView() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const [article, setArticle] = useState<Article | null>(null);

  // Animation values for drag-to-close
  const translateY = useRef(new Animated.Value(0)).current;
  const { height } = Dimensions.get('window');
  const DRAG_THRESHOLD = height * 0.25;

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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    const raw = getTempArticle(id);
    if (raw) {
      if (!raw.threatLevel) raw.threatLevel = getThreatLevel(raw as any);
      (raw as any).riskScore = generateConsistentRiskScore(raw);
      setArticle(raw);
    }
    setLoading(false);
  }, [id]);

  if (loading || !article) {
    return (
      <View style={[styles.loadingContainer, { backgroundColor: colors.background }]}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Text style={[styles.loadingText, { color: colors.textSecondary }]}>Loading article...</Text>
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
      
      <InstantView article={article} onBack={() => router.back()} />
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  dragIndicator: {
    width: 40,
    height: 4,
    borderRadius: 2,
    alignSelf: 'center',
    marginTop: 8,
    marginBottom: 8,
    opacity: 0.3,
  },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { ...Typography.body, marginTop: 16, fontSize: 16 },
});
