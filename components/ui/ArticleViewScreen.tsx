import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  StatusBar,
  Share,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';
import { useTheme } from '../../store/ThemeContext';
import { OptimizedImage } from './OptimizedImage';
import { formatFullDate } from '../../utils/dateUtils';
import { generateConsistentRiskScore, getThreatLevel, getThreatLevelColor } from '../../utils/threatAnalysis';
import type { Article } from '../../types/news';

interface ArticleViewScreenProps {
  article: Article;
  onBack: () => void;
}

export function ArticleViewScreen({ article, onBack }: ArticleViewScreenProps) {
  const { theme } = useTheme();
  const colors = Colors[theme === 'auto' ? 'light' : theme];

  const handleShare = async () => {
    try {
      await Share.share({
        message: `${article.title}\n\n${article.url}`,
        title: article.title,
      });
    } catch (error) {
      console.error('Error sharing article:', error);
    }
  };

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle={theme === 'dark' ? 'light-content' : 'dark-content'} />
      
      {/* Header Image */}
      <View style={styles.headerContainer}>
        {article.urlToImage ? (
          <OptimizedImage source={article.urlToImage} style={styles.headerImage} />
        ) : (
          <View style={[styles.placeholderHeader, { backgroundColor: colors.outline }]}>
            <Feather name="image" size={48} color={colors.textSecondary} />
          </View>
        )}
        
        {/* Header Overlay */}
        <LinearGradient
          colors={['rgba(0,0,0,0.6)', 'transparent']}
          style={styles.headerOverlay}
        />
        
        {/* Header Actions */}
        <View style={styles.headerActions}>
          <TouchableOpacity
            style={[styles.headerButton, { backgroundColor: 'rgba(0,0,0,0.5)' }]}
            onPress={onBack}
          >
            <Feather name="arrow-left" size={24} color="#FFFFFF" />
          </TouchableOpacity>
          
          <View style={styles.headerRightActions}>
            <TouchableOpacity
              style={[styles.headerButton, { backgroundColor: 'rgba(0,0,0,0.5)' }]}
              onPress={handleShare}
            >
              <Feather name="share" size={20} color="#FFFFFF" />
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* Content */}
      <ScrollView style={styles.scrollContent} showsVerticalScrollIndicator={false}>
        <View style={styles.contentContainer}>
          {/* Article Title */}
          <Text style={[styles.title, { color: colors.text }]}>
            {article.title}
          </Text>

          {/* Article Meta */}
          <View style={styles.meta}>
            <View style={styles.authorContainer}>
              <View style={[styles.authorAvatar, { backgroundColor: colors.secondary }]}>
                <Text style={[styles.authorInitial, { color: '#FFFFFF' }]}>
                  {article.author?.charAt(0) || article.source?.name?.charAt(0) || 'N'}
                </Text>
              </View>
              <View style={styles.authorInfo}>
                <Text style={[styles.authorName, { color: colors.text }]}>
                  {article.author || article.source?.name || 'Unknown Author'}
                </Text>
                <Text style={[styles.publishDate, { color: colors.textSecondary }]}>
                  {formatFullDate(article.publishedAt)}
                </Text>
              </View>
            </View>
          </View>

          {/* Threat Analysis */}
          <View style={[styles.threatSection, { backgroundColor: colors.surfaceContainer, borderColor: colors.outline }]}>
            <View style={styles.threatHeader}>
              <Feather name="shield" size={20} color={colors.primary} />
              <Text style={[styles.threatTitle, { color: colors.text }]}>
                Threat Analysis
              </Text>
            </View>
            <View style={styles.threatMetrics}>
              <View style={styles.threatMetric}>
                <Text style={[styles.metricLabel, { color: colors.textSecondary }]}>
                  Risk Level
                </Text>
                <View style={[styles.riskBadge, { backgroundColor: getThreatLevelColor(getThreatLevel(article), colors) }]}>
                  <Text style={[styles.riskText, { color: colors.onPrimary }]}>
                    {getThreatLevel(article).toUpperCase()}
                  </Text>
                </View>
              </View>
              <View style={styles.threatMetric}>
                <Text style={[styles.metricLabel, { color: colors.textSecondary }]}>
                  Risk Score
                </Text>
                <Text style={[styles.riskScore, { color: colors.text }]}>
                  {generateConsistentRiskScore(article)}/100
                </Text>
              </View>
            </View>
          </View>

          {/* AI Summary Section */}
          <View style={styles.articleContent}>
            {article.summary && (
              <View style={[styles.summaryContainer, { backgroundColor: colors.surface }]}>
                <View style={styles.summaryHeader}>
                  <View style={[styles.aiIconContainer, { backgroundColor: `${colors.primary}15` }]}>
                    <Feather name="zap" size={20} color={colors.primary} />
                  </View>
                  <View style={styles.summaryHeaderText}>
                    <Text style={[styles.summaryLabel, { color: colors.text }]}>
                      AI Summary
                    </Text>
                    <Text style={[styles.summarySubtitle, { color: colors.textSecondary }]}>
                      Key insights extracted for you
                    </Text>
                  </View>
                </View>
                
                <View style={[styles.summaryDivider, { backgroundColor: colors.outline }]} />
                
                <View style={styles.summaryContent}>
                  <Text style={[styles.summary, { color: colors.text }]}>
                    {(() => {
                      const summaryText = article.summary.trim();
                      const threatColor = getThreatLevelColor(getThreatLevel(article), colors);
                      
                      // Handle different headline patterns: **text**, *text*, or first sentence
                      const boldMatch = summaryText.match(/^\*\*(.*?)\*\*/);
                      const italicMatch = summaryText.match(/^\*(.*?)\*/);
                      
                      let firstSentence = '';
                      let remainingText = '';
                      
                      if (boldMatch) {
                        firstSentence = boldMatch[1];
                        remainingText = summaryText.replace(/^\*\*(.*?)\*\*\s*/, '');
                      } else if (italicMatch) {
                        firstSentence = italicMatch[1];
                        remainingText = summaryText.replace(/^\*(.*?)\*\s*/, '');
                      } else {
                        // Extract first sentence or first line
                        const sentences = summaryText.split(/(?<=[.!?])\s+/);
                        const lines = summaryText.split('\n');
                        
                        if (lines[0] && lines[0].length > 10 && lines[0].length < summaryText.length * 0.5) {
                          firstSentence = lines[0];
                          remainingText = summaryText.replace(lines[0], '').trim();
                        } else if (sentences[0] && sentences[0].length > 20) {
                          firstSentence = sentences[0];
                          remainingText = sentences.slice(1).join(' ');
                        } else {
                          firstSentence = summaryText.substring(0, Math.min(100, summaryText.indexOf('.') + 1)) || summaryText.substring(0, 100);
                          remainingText = summaryText.substring(firstSentence.length);
                        }
                      }
                      
                      return (
                        <>
                          {firstSentence && (
                            <Text style={[styles.summaryHighlight, { 
                              backgroundColor: `${threatColor}20`,
                              color: threatColor,
                              fontWeight: '700'
                            }]}>
                              {firstSentence.trim()}
                            </Text>
                          )}
                          {remainingText && (
                            <Text style={[styles.summary, { color: colors.text }]}>
                              {'\n\n' + remainingText.trim()}
                            </Text>
                          )}
                        </>
                      );
                    })()}
                  </Text>
                </View>
                
                <View style={[styles.summaryFooter, { backgroundColor: `${colors.primary}08` }]}>
                  <Feather name="cpu" size={14} color={colors.primary} />
                  <Text style={[styles.summaryFooterText, { color: colors.primary }]}>
                    AI-powered analysis
                  </Text>
                </View>
              </View>
            )}
          </View>

          {/* Footer Actions */}
          <View style={[styles.footer, { borderTopColor: colors.outline }]}>
            <TouchableOpacity style={styles.actionButton}>
              <Feather name="bookmark" size={20} color={colors.textSecondary} />
              <Text style={[styles.actionText, { color: colors.textSecondary }]}>Bookmark</Text>
            </TouchableOpacity>
            
            <TouchableOpacity style={styles.actionButton} onPress={handleShare}>
              <Feather name="share" size={20} color={colors.textSecondary} />
              <Text style={[styles.actionText, { color: colors.textSecondary }]}>
                Share
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  headerContainer: {
    position: 'relative',
    height: 250,
  },
  headerImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  placeholderHeader: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 100,
  },
  headerActions: {
    position: 'absolute',
    top: 50,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  headerRightActions: {
    flexDirection: 'row',
    gap: 12,
  },
  headerButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scrollContent: {
    flex: 1,
  },
  contentContainer: {
    paddingHorizontal: 20,
    paddingTop: 24,
    paddingBottom: 32,
  },
  title: {
    ...Typography.headlineLarge,
    marginBottom: 20,
  },
  meta: {
    marginBottom: 24,
  },
  authorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  authorAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  authorInitial: {
    ...Typography.button,
    fontSize: 16,
  },
  authorInfo: {
    flex: 1,
  },
  authorName: {
    ...Typography.bodySmall,
    fontWeight: '600',
    marginBottom: 2,
  },
  publishDate: {
    ...Typography.caption,
  },
  articleContent: {
    marginBottom: 32,
  },
  summaryContainer: {
    borderRadius: 16,
    overflow: 'hidden',
    marginBottom: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 6,
  },
  summaryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
  },
  aiIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  summaryHeaderText: {
    flex: 1,
    gap: 2,
  },
  summaryLabel: {
    ...Typography.titleMedium,
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: 0.15,
  },
  summarySubtitle: {
    ...Typography.bodySmall,
    fontSize: 12,
    opacity: 0.8,
  },
  summaryDivider: {
    height: 1,
    marginHorizontal: 16,
  },
  summaryContent: {
    padding: 16,
  },
  summary: {
    ...Typography.bodyLarge,
    fontSize: 16,
    lineHeight: 24,
    letterSpacing: 0.1,
  },
  summaryHighlight: {
    ...Typography.bodyLarge,
    fontSize: 16,
    lineHeight: 24,
    letterSpacing: 0.1,
    fontWeight: '700',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 6,
    marginBottom: 4,
    textAlign: 'left',
  },
  summaryFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    gap: 6,
  },
  summaryFooterText: {
    ...Typography.labelSmall,
    fontSize: 11,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  content: {
    ...Typography.body,
    lineHeight: 26,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 24,
    borderTopWidth: 1,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 16,
  },
  actionText: {
    ...Typography.bodySmall,
    marginLeft: 8,
    fontWeight: '500',
  },
  threatSection: {
    marginBottom: 24,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
  },
  threatHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  threatTitle: {
    ...Typography.titleMedium,
    marginLeft: 8,
  },
  threatMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  threatMetric: {
    alignItems: 'center',
  },
  metricLabel: {
    ...Typography.bodySmall,
    marginBottom: 4,
  },
  riskBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  riskText: {
    ...Typography.labelMedium,
    fontWeight: '600',
  },
  riskScore: {
    ...Typography.headlineSmall,
    fontWeight: 'bold',
  },
});