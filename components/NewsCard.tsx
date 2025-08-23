import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { router } from 'expo-router';
import { useState, memo, useCallback } from 'react';
import { useTheme } from '../store/ThemeContext';
import { BookmarkButton } from './BookmarkButton';
import { ShareSheet } from './ShareSheet';
import { OptimizedImage } from './ui/OptimizedImage';
import { Colors } from '../constants/Colors';
import { formatDate } from '../utils/dateUtils';
import { generateConsistentRiskScore, getThreatLevel, getThreatLevelColor } from '../utils/threatAnalysis';
import type { Article } from '../types/news';
import { Feather, MaterialIcons } from '@expo/vector-icons';

// const { width } = Dimensions.get('window');

function NewsCardComponent({ article }: { article: Article }) {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const [isLiked, setIsLiked] = useState(false);
  const [isDisliked, setIsDisliked] = useState(false);
  const [likeCount, setLikeCount] = useState(Math.floor(Math.random() * 50) + 10); // Random initial likes

  const handlePress = useCallback(() => {
    router.push(`/article-view/${encodeURIComponent(article.url)}`);
  }, [article.url]);

  // Get source-specific badge color
  const getSourceBadgeColor = useCallback((url: string) => {
    try {
      const domain = new URL(url).hostname.toLowerCase();
      const colorMap: { [key: string]: string } = {
        'threatpost.com': '#FF6B6B',      // Red
        'bleepingcomputer.com': '#4ECDC4', // Teal
        'krebsonsecurity.com': '#45B7D1',  // Blue  
        'darkreading.com': '#8E44AD',      // Purple
        'securityweek.com': '#F39C12',     // Orange
        'thehackernews.com': '#27AE60',    // Green
        'cyberscoop.com': '#E74C3C',       // Dark Red
        'securityboulevard.com': '#3498DB', // Light Blue
        'infosecurity-magazine.com': '#9B59B6', // Light Purple
        'default': '#10B981'               // Default Green
      };
      
      for (const [key, color] of Object.entries(colorMap)) {
        if (domain.includes(key.split('.')[0])) {
          return color;
        }
      }
      return colorMap.default;
    } catch {
      return '#10B981'; // Default green
    }
  }, []);

  const handleLike = useCallback(() => {
    if (isLiked) {
      setIsLiked(false);
      setLikeCount(prev => prev - 1);
    } else {
      setIsLiked(true);
      setIsDisliked(false);
      setLikeCount(prev => prev + (isDisliked ? 2 : 1));
    }
  }, [isLiked, isDisliked]);

  const handleDislike = useCallback(() => {
    if (isDisliked) {
      setIsDisliked(false);
      setLikeCount(prev => prev + 1);
    } else {
      setIsDisliked(true);
      setIsLiked(false);
      setLikeCount(prev => prev - (isLiked ? 2 : 1));
    }
  }, [isLiked, isDisliked]);

  // Use consistent threat analysis utilities
  const riskScore = generateConsistentRiskScore(article);
  const threatLevel = getThreatLevel(article);
  const threatColor = getThreatLevelColor(threatLevel, colors);

  // Clean up description text by removing markdown formatting
  const cleanDescription = (text: string) => {
    if (!text) return text;
    return text
      .replace(/\*\*(.*?)\*\*/g, '$1') // Remove **bold** formatting
      .replace(/\*(.*?)\*/g, '$1')     // Remove *italic* formatting
      .replace(/_{2,}(.*?)_{2,}/g, '$1') // Remove __underline__ formatting
      .replace(/`(.*?)`/g, '$1')       // Remove `code` formatting
      .replace(/#{1,6}\s/g, '')        // Remove # headers
      .trim();
  };

  return (
    <TouchableOpacity
      style={[styles.card, { 
        backgroundColor: colors.card,
      }]}
      onPress={handlePress}
      activeOpacity={0.8}
    >
      {article.urlToImage ? (
        <OptimizedImage source={article.urlToImage} style={styles.image} />
      ) : (
        <View style={[styles.placeholderImage, { backgroundColor: colors.cardBorder }]}>
          <Feather name="image" size={32} color={colors.textSecondary} />
        </View>
      )}

      {/* Source Badge - Top Left with dynamic colors */}
      <View style={[styles.sourceBadge, { backgroundColor: getSourceBadgeColor(article.url) }]}>
        <Text style={styles.sourceBadgeText}>
          {new URL(article.url).hostname}
        </Text>
      </View>

      {/* Threat Level Badge - Top Right */}
      <View style={[styles.threatBadge, { backgroundColor: threatColor }]}>
        <Text style={[styles.threatBadgeText, { color: colors.onPrimary }]}>
          {threatLevel.toUpperCase()}
        </Text>
      </View>

      <View style={styles.content}>
        <TouchableOpacity onPress={handlePress}>
          <Text style={[styles.title, { color: colors.text }]} numberOfLines={2}>
            {article.title}
          </Text>
        </TouchableOpacity>

        {(article.summary || article.description) && (
          <Text
            style={[styles.description, { color: colors.textSecondary }]}
            numberOfLines={2}
          >
            {cleanDescription(article.summary || article.description || '')}
          </Text>
        )}

        {/* Risk Score with AI badge - Reduced spacing */}
        <View style={styles.riskSection}>
          <View style={styles.riskRow}>
            <Feather name="shield" size={16} color={colors.primary} />
            <Text style={[styles.riskScore, { color: colors.primary }]}>
              Risk Score: {riskScore}% • AI Analyzed
            </Text>
          </View>
        </View>

        {/* Bottom Row - Enhanced with Like/Dislike */}
        <View style={styles.bottomRow}>
          <View style={styles.timeRow}>
            <Feather name="clock" size={14} color={colors.textSecondary} />
            <Text style={[styles.timeAgo, { color: colors.textSecondary }]}>
              {formatDate(article.publishedAt)}
            </Text>
            <View style={[styles.riskIndicator, { backgroundColor: threatColor }]}>
              <Text style={styles.riskPercentage}>{riskScore}%</Text>
            </View>
          </View>
          
          <View style={styles.actions}>
            {/* Like/Dislike Buttons */}
            <View style={styles.likeDislikeContainer}>
              <TouchableOpacity 
                onPress={handleLike}
                style={[styles.likeButton, isLiked && styles.likeButtonActive]}
                activeOpacity={0.7}
              >
                <MaterialIcons 
                  name={isLiked ? "thumb-up" : "thumb-up-off-alt"} 
                  size={16} 
                  color={isLiked ? colors.primary : colors.textSecondary} 
                />
                <Text style={[styles.likeCount, { 
                  color: isLiked ? colors.primary : colors.textSecondary 
                }]}>
                  {likeCount}
                </Text>
              </TouchableOpacity>
              
              <TouchableOpacity 
                onPress={handleDislike}
                style={[styles.dislikeButton, isDisliked && styles.dislikeButtonActive]}
                activeOpacity={0.7}
              >
                <MaterialIcons 
                  name={isDisliked ? "thumb-down" : "thumb-down-off-alt"} 
                  size={16} 
                  color={isDisliked ? colors.error : colors.textSecondary} 
                />
              </TouchableOpacity>
            </View>
            
            <ShareSheet article={article} />
            <BookmarkButton article={article} />
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 16,
    overflow: 'hidden',
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    position: 'relative',
  },
  image: {
    width: '100%',
    height: 200,
    resizeMode: 'cover',
  },
  placeholderImage: {
    width: '100%',
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
  },
  sourceBadge: {
    position: 'absolute',
    top: 12,
    left: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    elevation: 2,
  },
  sourceBadgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: '600',
    textTransform: 'lowercase',
  },
  threatBadge: {
    position: 'absolute',
    top: 12,
    right: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    elevation: 2,
  },
  threatBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  content: {
    padding: 16,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    lineHeight: 22,
    marginBottom: 8,
  },
  description: {
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 8, // Reduced from 4
  },
  riskSection: {
    marginBottom: 10, // Reduced from 12
  },
  riskRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  riskScore: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 6,
  },
  bottomRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  timeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  timeAgo: {
    fontSize: 12,
    marginLeft: 4,
    marginRight: 8,
  },
  riskIndicator: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    marginRight: 4,
  },
  riskPercentage: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  actions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12, // Increased gap for better spacing
  },
  likeDislikeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 8,
  },
  likeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: 'transparent',
    marginRight: 4,
  },
  likeButtonActive: {
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
  },
  dislikeButton: {
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 4,
    borderRadius: 12,
    backgroundColor: 'transparent',
  },
  dislikeButtonActive: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
  },
  likeCount: {
    fontSize: 12,
    fontWeight: '600',
    marginLeft: 4,
  },
});

// Export the memoized component
export const NewsCard = memo(NewsCardComponent);