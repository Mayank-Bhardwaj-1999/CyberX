import React, { useRef, useEffect, useState, useMemo } from 'react';
import {
  View,
  ScrollView,
  Text,
  TouchableOpacity,
  PanResponder,
  Animated,
  Dimensions,
  SafeAreaView,
  Share,
  Alert,
  StatusBar,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { BlurView } from 'expo-blur';
import { useTheme } from '../../store/ThemeContext';
import { useBookmarks } from '../../hooks/useBookmarks';
import type { Article } from '../../types/news';

const { width, height } = Dimensions.get('window');

interface ModernArticleViewScreenProps {
  article: Article;
  onBack?: () => void;
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString);
  if (isNaN(date.getTime())) {
    return 'Unknown date';
  }
  
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays === 1) {
    return 'Yesterday';
  } else if (diffDays <= 7) {
    return `${diffDays} days ago`;
  } else {
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  }
};

const stripHtml = (html: string) => {
  return html.replace(/<[^>]*>/g, '').replace(/&[^;]+;/g, '');
};

export function ModernArticleViewScreen({ article, onBack }: ModernArticleViewScreenProps) {
  const router = useRouter();
  const { theme, colors } = useTheme();
  const { isBookmarked, addBookmark, removeBookmark } = useBookmarks();
  const [scrollY] = useState(new Animated.Value(0));
  const [dragY] = useState(new Animated.Value(0));
  const [isDragging, setIsDragging] = useState(false);
  
  const bookmarked = isBookmarked(article.title);
  
  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, gestureState) => {
        return Math.abs(gestureState.dy) > 10 && Math.abs(gestureState.dy) > Math.abs(gestureState.dx);
      },
      onPanResponderGrant: () => {
        setIsDragging(true);
      },
      onPanResponderMove: (_, gestureState) => {
        if (gestureState.dy > 0) {
          dragY.setValue(gestureState.dy);
        }
      },
      onPanResponderRelease: (_, gestureState) => {
        setIsDragging(false);
        
        if (gestureState.dy > 100) {
          Animated.timing(dragY, {
            toValue: height,
            duration: 300,
            useNativeDriver: true,
          }).start(() => {
            if (onBack) {
              onBack();
            } else {
              router.back();
            }
          });
        } else {
          Animated.spring(dragY, {
            toValue: 0,
            useNativeDriver: true,
          }).start();
        }
      },
      onPanResponderTerminate: () => {
        setIsDragging(false);
        Animated.spring(dragY, {
          toValue: 0,
          useNativeDriver: true,
        }).start();
      },
    })
  ).current;

  const headerOpacity = scrollY.interpolate({
    inputRange: [0, 100],
    outputRange: [0, 1],
    extrapolate: 'clamp',
  });

  const handleShare = async () => {
    try {
      await Share.share({
        message: `${article.title}\n\n${article.summary || stripHtml(article.description)}\n\nRead more: ${article.url}`,
        url: article.url,
        title: article.title,
      });
    } catch (error) {
      console.error('Error sharing:', error);
      Alert.alert('Error', 'Unable to share article');
    }
  };

  const handleBookmark = () => {
    if (bookmarked) {
      removeBookmark(article.title);
    } else {
      addBookmark(article);
    }
  };

  const cleanContent = useMemo(() => {
    if (article.content) {
      return stripHtml(article.content);
    }
    if (article.description) {
      return stripHtml(article.description);
    }
    return article.summary || 'No content available';
  }, [article]);

  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <StatusBar hidden />
      
      <Animated.View 
        style={{ 
          flex: 1,
          transform: [{ translateY: dragY }]
        }}
        {...panResponder.panHandlers}
      >
        <SafeAreaView style={{ flex: 1 }}>
          {/* Drag Indicator */}
          <View style={[styles.dragIndicator, { backgroundColor: colors.textSecondary }]} />
          
          {/* Header */}
          <View style={[styles.header, { borderBottomColor: colors.border }]}>
            <TouchableOpacity
              onPress={() => {
                if (onBack) {
                  onBack();
                } else {
                  router.back();
                }
              }}
              style={[styles.headerButton, { backgroundColor: colors.cardBackground }]}
            >
              <Ionicons name="chevron-back" size={24} color={colors.text} />
            </TouchableOpacity>
            
            <View style={styles.headerActions}>
              <TouchableOpacity
                onPress={handleBookmark}
                style={[styles.headerButton, { backgroundColor: colors.cardBackground }]}
              >
                <Ionicons 
                  name={bookmarked ? "bookmark" : "bookmark-outline"} 
                  size={20} 
                  color={bookmarked ? colors.primary : colors.text} 
                />
              </TouchableOpacity>
              
              <TouchableOpacity
                onPress={handleShare}
                style={[styles.headerButton, { backgroundColor: colors.cardBackground, marginLeft: 8 }]}
              >
                <Ionicons name="share-outline" size={20} color={colors.text} />
              </TouchableOpacity>
            </View>
          </View>

          <ScrollView
            style={{ flex: 1 }}
            contentContainerStyle={{ paddingBottom: 100 }}
            showsVerticalScrollIndicator={false}
            onScroll={Animated.event(
              [{ nativeEvent: { contentOffset: { y: scrollY } } }],
              { useNativeDriver: false }
            )}
            scrollEventThrottle={16}
          >
            {/* Article Content */}
            <View style={styles.content}>
              {/* Title */}
              <Text style={[styles.title, { color: colors.text }]}>
                {article.title}
              </Text>
              
              {/* Meta Info */}
              <View style={styles.metaInfo}>
                <Text style={[styles.source, { color: colors.primary }]}>
                  {article.source || 'Unknown Source'}
                </Text>
                <Text style={[styles.date, { color: colors.textSecondary }]}>
                  • {formatDate(article.publishedAt || article.pubDate || '')}
                </Text>
              </View>
              
              {/* Summary */}
              {article.summary && (
                <View style={[styles.summaryContainer, { backgroundColor: colors.cardBackground }]}>
                  <Text style={[styles.summaryLabel, { color: colors.primary }]}>
                    Summary
                  </Text>
                  <Text style={[styles.summary, { color: colors.text }]}>
                    {article.summary}
                  </Text>
                </View>
              )}
              
              {/* Main Content */}
              <Text style={[styles.articleContent, { color: colors.text }]}>
                {cleanContent}
              </Text>
              
              {/* Tags */}
              {article.keywords && article.keywords.length > 0 && (
                <View style={styles.tagsContainer}>
                  <Text style={[styles.tagsLabel, { color: colors.textSecondary }]}>
                    Related Topics:
                  </Text>
                  <View style={styles.tagsWrapper}>
                    {article.keywords.slice(0, 5).map((tag, index) => (
                      <View
                        key={index}
                        style={[styles.tag, { backgroundColor: colors.primary + '20' }]}
                      >
                        <Text style={[styles.tagText, { color: colors.primary }]}>
                          #{tag}
                        </Text>
                      </View>
                    ))}
                  </View>
                </View>
              )}
            </View>
          </ScrollView>
        </SafeAreaView>
      </Animated.View>
    </View>
  );
}

const styles = {
  dragIndicator: {
    width: 40,
    height: 4,
    borderRadius: 2,
    alignSelf: 'center',
    marginTop: 8,
    marginBottom: 8,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 0.5,
  },
  headerButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  content: {
    padding: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    lineHeight: 36,
    marginBottom: 16,
    fontFamily: 'Inter-Bold',
  },
  metaInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 24,
  },
  source: {
    fontSize: 14,
    fontWeight: '600',
    fontFamily: 'Inter-SemiBold',
  },
  date: {
    fontSize: 14,
    marginLeft: 4,
    fontFamily: 'Inter-Regular',
  },
  summaryContainer: {
    padding: 20,
    borderRadius: 16,
    marginBottom: 24,
    borderLeftWidth: 4,
    borderLeftColor: '#3B82F6',
  },
  summaryLabel: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 12,
    fontFamily: 'Inter-SemiBold',
  },
  summary: {
    fontSize: 16,
    lineHeight: 24,
    fontFamily: 'Inter-Regular',
  },
  articleContent: {
    fontSize: 17,
    lineHeight: 28,
    marginBottom: 32,
    fontFamily: 'Inter-Regular',
  },
  tagsContainer: {
    marginTop: 24,
  },
  tagsLabel: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 12,
    fontFamily: 'Inter-SemiBold',
  },
  tagsWrapper: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  tag: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  tagText: {
    fontSize: 12,
    fontWeight: '500',
    fontFamily: 'Inter-Medium',
  },
};
