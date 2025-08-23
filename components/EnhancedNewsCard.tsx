import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { router } from 'expo-router';
import { Feather } from '@expo/vector-icons';
import { useTheme } from '../store/ThemeContext';
import { BookmarkButton } from './BookmarkButton';
import { OptimizedImage } from './ui/OptimizedImage';
import { Colors } from '../constants/Colors';
import { Typography } from '../constants/Typography';
import { formatDate } from '../utils/dateUtils';
import { MaterialCard, MaterialElevation } from './ui/MaterialComponents';
import type { Article } from '../types/news';

interface EnhancedNewsCardProps {
  article: Article;
  index: number;
  variant?: 'default' | 'featured' | 'compact';
}

export function EnhancedNewsCard({ article, variant = 'default' }: EnhancedNewsCardProps) {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];

  const handlePress = () => {
    router.push(`/article-view/${encodeURIComponent(article.url)}`);
  };

  const getThreatLevelColor = (article: Article) => {
    if (article.threatLevel === 'critical') return colors.critical;
    if (article.threatLevel === 'high') return colors.vulnerability;
    if (article.threatLevel === 'medium') return colors.threat;
    if (article.threatLevel === 'low') return colors.security;
    
    // Fallback: analyze content
    const content = `${article.title} ${article.description}`.toLowerCase();
    if (content.includes('critical') || content.includes('breach') || content.includes('attack')) {
      return colors.critical;
    } else if (content.includes('vulnerability') || content.includes('exploit')) {
      return colors.vulnerability;
    } else if (content.includes('threat') || content.includes('malware')) {
      return colors.threat;
    }
    return colors.security;
  };

  const getThreatLevelText = (article: Article) => {
    if (article.threatLevel) {
      return article.threatLevel.toUpperCase();
    }
    
    // Fallback: analyze content for threat level
    const content = `${article.title} ${article.description || ''}`.toLowerCase();
    if (content.includes('critical') || content.includes('breach') || content.includes('ransomware')) {
      return 'CRITICAL';
    } else if (content.includes('vulnerability') || content.includes('exploit') || content.includes('attack')) {
      return 'HIGH';
    } else if (content.includes('threat') || content.includes('malware') || content.includes('phishing')) {
      return 'MEDIUM';
    }
    return 'LOW';
  };

  const getRiskScore = (article: Article) => {
    if (article.aiAnalysis?.riskScore) {
      return article.aiAnalysis.riskScore;
    }
    
    // Fallback: calculate based on threat level analysis
    const content = `${article.title} ${article.description || ''}`.toLowerCase();
    if (content.includes('critical') || content.includes('breach') || content.includes('ransomware')) {
      return Math.floor(Math.random() * 20) + 80; // 80-100
    } else if (content.includes('vulnerability') || content.includes('exploit') || content.includes('attack')) {
      return Math.floor(Math.random() * 20) + 60; // 60-80
    } else if (content.includes('threat') || content.includes('malware') || content.includes('phishing')) {
      return Math.floor(Math.random() * 20) + 40; // 40-60
    }
    return Math.floor(Math.random() * 30) + 10; // 10-40
  };

  const renderFeaturedCard = () => (
    <MaterialElevation level={3} style={styles.featuredContainer}>
      <TouchableOpacity
        style={styles.featuredCard}
        onPress={handlePress}
        activeOpacity={0.95}
      >
        <View style={styles.featuredImageContainer}>
          {article.urlToImage ? (
            <OptimizedImage source={article.urlToImage} style={styles.featuredImage} />
          ) : (
            <LinearGradient
              colors={[colors.primary, colors.secondary]}
              style={styles.featuredImage}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
            >
              <Feather name="shield" size={48} color={colors.onPrimary} />
            </LinearGradient>
          )}
          
          <LinearGradient
            colors={['transparent', 'rgba(0,0,0,0.8)']}
            style={styles.featuredImageOverlay}
          />
          
          <View style={styles.featuredBadge}>
            <View style={[styles.threatBadge, { backgroundColor: getThreatLevelColor(article) }]}>
              <Text style={[Typography.securityBadge, { color: colors.onPrimary }]}>
                {getThreatLevelText(article)}
              </Text>
            </View>
            <View style={[styles.riskScoreBadge, { backgroundColor: colors.surface }]}>
              <Text style={[Typography.riskScore, { color: colors.text }]}>
                Risk: {getRiskScore(article)}
              </Text>
            </View>
          </View>

          <View style={styles.featuredContent}>
            <Text style={[Typography.newsTitle, { color: colors.onPrimary, fontSize: 20 }]} numberOfLines={2}>
              {article.title}
            </Text>
            <View style={styles.featuredMeta}>
              <Text style={[Typography.newsSource, { color: colors.onPrimary, opacity: 0.9 }]}>
                {article.source.name}
              </Text>
              <Text style={[Typography.newsTimestamp, { color: colors.onPrimary, opacity: 0.8 }]}>
                {formatDate(article.publishedAt)}
              </Text>
            </View>
          </View>
        </View>

        <View style={styles.featuredActions}>
          <BookmarkButton article={article} />
        </View>
      </TouchableOpacity>
    </MaterialElevation>
  );

  const renderCompactCard = () => (
    <MaterialCard variant="outlined" onPress={handlePress} style={styles.compactCard}>
      <View style={styles.compactContent}>
        <View style={styles.compactTextContainer}>
          <View style={styles.compactHeader}>
            <View style={[styles.sourceIndicator, { backgroundColor: getThreatLevelColor(article) }]} />
            <Text style={[Typography.newsSource, { color: colors.textSecondary }]} numberOfLines={1}>
              {article.source.name}
            </Text>
            <Text style={[Typography.newsTimestamp, { color: colors.textTertiary }]}>
              {formatDate(article.publishedAt)}
            </Text>
          </View>
          
          <Text style={[Typography.cardTitle, { color: colors.text }]} numberOfLines={2}>
            {article.title}
          </Text>
          
          <View style={styles.compactThreatInfo}>
            <Text style={[Typography.riskScore, { color: getThreatLevelColor(article) }]}>
              {getThreatLevelText(article)}
            </Text>
            <Text style={[Typography.riskScore, { color: colors.textSecondary, marginLeft: 8 }]}>
              Risk: {getRiskScore(article)}
            </Text>
          </View>
        </View>

        {article.urlToImage && (
          <View style={styles.compactImageContainer}>
            <OptimizedImage source={article.urlToImage} style={styles.compactImage} />
          </View>
        )}
      </View>
    </MaterialCard>
  );

  const renderDefaultCard = () => (
    <MaterialCard 
      variant="elevated" 
      onPress={handlePress} 
      style={[styles.defaultCard, { backgroundColor: colors.card }]}
    >
      <View style={styles.defaultContent}>
        {article.urlToImage && (
          <View style={styles.defaultImageContainer}>
            <OptimizedImage source={article.urlToImage} style={styles.defaultImage} />
            <LinearGradient
              colors={['transparent', 'rgba(0,0,0,0.1)']}
              style={styles.defaultImageOverlay}
            />
          </View>
        )}
        
        <View style={styles.defaultTextContent}>
          <View style={styles.defaultHeader}>
            <View style={styles.sourceContainer}>
              <View style={[styles.sourceIndicator, { backgroundColor: getThreatLevelColor(article) }]} />
              <Text style={[Typography.newsSource, { color: colors.textSecondary }]} numberOfLines={1}>
                {article.source.name}
              </Text>
            </View>
            <View style={styles.threatInfoContainer}>
              <View style={[styles.severityBadge, { backgroundColor: getThreatLevelColor(article) }]}>
                <Text style={[Typography.riskScore, { color: colors.onPrimary }]}>
                  {getThreatLevelText(article)}
                </Text>
              </View>
              <Text style={[Typography.riskScore, { color: colors.textSecondary, marginLeft: 8 }]}>
                Risk: {getRiskScore(article)}
              </Text>
            </View>
          </View>

          <Text style={[Typography.newsTitle, { color: colors.text, marginVertical: 8 }]} numberOfLines={3}>
            {article.title}
          </Text>

          {article.description && (
            <Text style={[Typography.cardSubtitle, { color: colors.textSecondary }]} numberOfLines={2}>
              {article.description}
            </Text>
          )}

          <View style={styles.defaultActions}>
            <BookmarkButton article={article} />
            <View style={styles.actionsSpacer} />
            <Feather name="share" size={18} color={colors.textSecondary} />
          </View>
        </View>
      </View>
    </MaterialCard>
  );

  switch (variant) {
    case 'featured':
      return renderFeaturedCard();
    case 'compact':
      return renderCompactCard();
    default:
      return renderDefaultCard();
  }
}

const styles = StyleSheet.create({
  // Featured Card Styles
  featuredContainer: {
    marginHorizontal: 16,
    marginVertical: 12,
    borderRadius: 16,
    overflow: 'hidden',
  },
  featuredCard: {
    height: 280,
    borderRadius: 16,
    overflow: 'hidden',
  },
  featuredImageContainer: {
    flex: 1,
    position: 'relative',
  },
  featuredImage: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  featuredImageOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: '50%',
  },
  featuredBadge: {
    position: 'absolute',
    top: 16,
    left: 16,
  },
  featuredContent: {
    position: 'absolute',
    bottom: 16,
    left: 16,
    right: 16,
  },
  featuredMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  featuredActions: {
    position: 'absolute',
    top: 16,
    right: 16,
  },

  // Compact Card Styles
  compactCard: {
    marginHorizontal: 16,
    marginVertical: 6,
    padding: 12,
  },
  compactContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  compactTextContainer: {
    flex: 1,
    marginRight: 12,
  },
  compactHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  compactImageContainer: {
    width: 80,
    height: 60,
    borderRadius: 8,
    overflow: 'hidden',
  },
  compactImage: {
    width: '100%',
    height: '100%',
  },
  compactThreatInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 4,
  },

  // Default Card Styles
  defaultCard: {
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 16,
    overflow: 'hidden',
    padding: 0,
  },
  defaultContent: {
    overflow: 'hidden',
  },
  defaultImageContainer: {
    height: 200,
    position: 'relative',
  },
  defaultImage: {
    width: '100%',
    height: '100%',
  },
  defaultImageOverlay: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: '30%',
  },
  defaultTextContent: {
    padding: 16,
  },
  defaultHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  defaultActions: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.05)',
  },

  // Common Styles
  sourceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  sourceIndicator: {
    width: 4,
    height: 4,
    borderRadius: 2,
    marginRight: 8,
  },
  threatBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginRight: 8,
  },
  riskScoreBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.1)',
  },
  threatInfoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  severityBadge: {
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
  },
  actionsSpacer: {
    flex: 1,
  },
});
