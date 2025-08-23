import { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialIcons } from '@expo/vector-icons';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';
import { BookmarkButton } from '../BookmarkButton';
import { OptimizedImage } from './OptimizedImage';
// ShareSheet import removed as it's not used
import { formatFullDate } from '../../utils/dateUtils';
import { generateConsistentRiskScore, getThreatLevel, getThreatLevelColor } from '../../utils/threatAnalysis';
import { storage } from '../../services/storage';
import type { Article } from '../../types/news';
import { SimpleWebViewModal } from './SimpleWebViewModal';

// Dimensions removed as not used

interface ModernArticleViewScreenProps {
  article: Article;
  onBack: () => void;
}

export function ModernArticleViewScreen({ article, onBack }: ModernArticleViewScreenProps) {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const [isOffline, setIsOffline] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);

  // Get consistent threat analysis for this article
  const riskScore = generateConsistentRiskScore(article);
  const threatLevel = getThreatLevel(article);
  const threatColor = getThreatLevelColor(threatLevel, colors);

  // Check if article is available offline
  useEffect(() => {
    checkOfflineStatus();
  }, [article.url]);

  const checkOfflineStatus = async () => {
    const offline = await storage.isArticleOffline(article.url);
    setIsOffline(offline);
  };

  const handleSaveForOffline = async () => {
    try {
      await storage.saveArticleForOffline(article);
      setIsOffline(true);
      Alert.alert('Success', 'Article saved for offline reading');
    } catch (error) {
      Alert.alert('Error', 'Failed to save article for offline reading');
    }
  };

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]} edges={['top', 'left', 'right', 'bottom']}>
      {/* Custom Header */}
      <View style={[styles.headerContainer, { backgroundColor: colors.surface }]}>
        <View style={styles.header}>
          <TouchableOpacity onPress={onBack} style={styles.backButton}>
            <MaterialIcons name="arrow-back" size={24} color={colors.text} />
          </TouchableOpacity>
          
          <Text style={[styles.headerTitle, { color: colors.text }]} numberOfLines={1}>
            {article.source.name || 'Article'}
          </Text>
          
          <View style={styles.headerActions}>
            {/* Offline Button */}
            <TouchableOpacity
              style={[styles.headerButton, { backgroundColor: colors.surface }]}
              onPress={handleSaveForOffline}
            >
              <MaterialIcons 
                name={isOffline ? "offline-bolt" : "cloud-download"} 
                size={20} 
                color={isOffline ? colors.success : colors.textSecondary} 
              />
            </TouchableOpacity>

            {/* Bookmark Button */}
            <BookmarkButton article={article} />
          </View>
        </View>
      </View>
      
      <ScrollView 
        style={styles.scrollView}
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scrollContent}
      >
        {/* Hero Image */}
        <View style={styles.heroContainer}>
          {article.urlToImage ? (
            <OptimizedImage source={article.urlToImage} style={styles.heroImage} />
          ) : (
            <View style={[styles.placeholderImage, { backgroundColor: colors.cardBorder }]}>
              <MaterialIcons name="security" size={48} color={colors.textSecondary} />
            </View>
          )}
          
          {/* Overlay with threat level */}
          <View style={[styles.overlay, { backgroundColor: `${threatColor}20` }]}>
            <View style={[styles.threatLevelBadge, { backgroundColor: threatColor }]}>
              <MaterialIcons name={threatLevel === 'critical' ? 'warning' : threatLevel === 'high' ? 'error' : 'info'} size={16} color="#FFFFFF" />
              <Text style={styles.threatLevelText}>{threatLevel.toUpperCase()}</Text>
            </View>
          </View>
        </View>

        {/* Content */}
        <View style={styles.content}>
          {/* Title */}
          <Text style={[styles.title, { color: colors.text }]}>
            {article.title}
          </Text>

          {/* Metadata */}
          <View style={styles.metadata}>
            <View style={styles.metadataItem}>
              <MaterialIcons name="schedule" size={16} color={colors.textSecondary} />
              <Text style={[styles.metadataText, { color: colors.textSecondary }]}>
                {formatFullDate(article.publishedAt)}
              </Text>
            </View>
            
            {article.author && (
              <View style={styles.metadataItem}>
                <MaterialIcons name="person" size={16} color={colors.textSecondary} />
                <Text style={[styles.metadataText, { color: colors.textSecondary }]}>
                  {article.author}
                </Text>
              </View>
            )}
            
            <View style={styles.metadataItem}>
              <MaterialIcons name="article" size={16} color={colors.textSecondary} />
              <Text style={[styles.metadataText, { color: colors.textSecondary }]}>
                {article.source.name}
              </Text>
            </View>

            {/* Offline Status */}
            {isOffline && (
              <View style={styles.metadataItem}>
                <MaterialIcons name="cloud-done" size={16} color={colors.success} />
                <Text style={[styles.metadataText, { color: colors.success }]}>
                  Offline
                </Text>
              </View>
            )}
          </View>

          {/* Threat Analysis Card */}
          <View style={[styles.analysisCard, { backgroundColor: colors.surface }]}>
            <View style={styles.analysisHeader}>
              <MaterialIcons name="security" size={20} color={colors.primary} />
              <Text style={[styles.analysisTitle, { color: colors.text }]}>
                Threat Analysis
              </Text>
            </View>
            
            <View style={styles.analysisContent}>
              {/* Risk Score */}
              <View style={styles.riskScoreSection}>
                <Text style={[styles.riskScoreLabel, { color: colors.textSecondary }]}>
                  Risk Score
                </Text>
                <View style={styles.riskScoreContainer}>
                  <Text style={[styles.riskScore, { color: threatColor }]}>
                    {riskScore}%
                  </Text>
                  <View style={[styles.riskBar, { backgroundColor: colors.cardBorder }]}>
                    <View 
                      style={[
                        styles.riskBarFill, 
                        { 
                          backgroundColor: threatColor,
                          width: `${riskScore}%`
                        }
                      ]} 
                    />
                  </View>
                </View>
              </View>

              {/* Simplified threat analysis */}
              <View style={styles.recommendationsSection}>
                <Text style={[styles.sectionLabel, { color: colors.textSecondary }]}>
                  Threat Level: {threatLevel.toUpperCase()} (Risk: {riskScore}%)
                </Text>
              </View>
            </View>
          </View>

          {/* AI Summary */}
          {article.summary && (
            <View style={[styles.summaryCard, { backgroundColor: colors.surface }]}>
              <View style={styles.summaryHeader}>
                <View style={[styles.aiIconContainer, { backgroundColor: `${colors.primary}15` }]}>
                  <MaterialIcons name="auto-awesome" size={24} color={colors.primary} />
                </View>
                <View style={styles.summaryHeaderText}>
                  <Text style={[styles.summaryTitle, { color: colors.text }]}>
                    AI Summary
                  </Text>
                  <Text style={[styles.summarySubtitle, { color: colors.textSecondary }]}>
                    Key insights extracted for you
                  </Text>
                </View>
              </View>
              
              <View style={styles.summaryDivider} />
              
              <View style={styles.summaryContent}>
                <Text style={[styles.summaryText, { color: colors.text }]}>
                  {(() => {
                    const summaryText = article.summary.trim();
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
                          <Text style={[styles.summaryText, { color: colors.text }]}>
                            {'\n\n' + remainingText.trim()}
                          </Text>
                        )}
                      </>
                    );
                  })()}
                </Text>
              </View>
              
              <View style={[styles.summaryFooter, { backgroundColor: `${colors.primary}08` }]}>
                <MaterialIcons name="lightbulb" size={16} color={colors.primary} />
                <Text style={[styles.summaryFooterText, { color: colors.primary }]}>
                  AI-powered analysis
                </Text>
              </View>
            </View>
          )}

          {/* CTA Buttons */}
          <View style={styles.ctaContainer}>
            <TouchableOpacity 
              style={[styles.ctaButton, { backgroundColor: colors.primary }]}
              onPress={() => setModalVisible(true)}
            >
              <MaterialIcons name="open-in-new" size={20} color={colors.onPrimary} />
              <Text style={[styles.ctaButtonText, { color: colors.onPrimary }]}>
                Read Full Article
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </ScrollView>

      {/* Stable WebView Modal */}
      <SimpleWebViewModal
        visible={modalVisible}
        url={article.url}
        onClose={() => setModalVisible(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  headerContainer: {
    backgroundColor: 'transparent',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    flex: 1,
    textAlign: 'center',
    marginHorizontal: 16,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.1)',
  },
  backButton: {
    padding: 8,
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
  },
  shareButton: {
    padding: 8,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 32,
  },
  heroContainer: {
    position: 'relative',
    height: 250,
    width: '100%',
  },
  heroImage: {
    width: '100%',
    height: '100%',
  },
  placeholderImage: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  overlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'flex-end',
    alignItems: 'flex-end',
    padding: 16,
  },
  threatLevelBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    gap: 6,
  },
  threatLevelText: {
    ...Typography.labelSmall,
    fontSize: 12,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  content: {
    padding: 16,
  },
  title: {
    ...Typography.headlineMedium,
    fontSize: 24,
    fontWeight: '700',
    lineHeight: 32,
    marginBottom: 16,
  },
  metadata: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
    marginBottom: 24,
  },
  metadataItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  metadataText: {
    ...Typography.bodySmall,
    fontSize: 14,
  },
  analysisCard: {
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  analysisHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  analysisTitle: {
    ...Typography.titleMedium,
    fontSize: 18,
    fontWeight: '600',
  },
  analysisContent: {
    gap: 16,
  },
  riskScoreSection: {
    gap: 8,
  },
  riskScoreLabel: {
    ...Typography.labelMedium,
    fontSize: 14,
  },
  riskScoreContainer: {
    gap: 8,
  },
  riskScore: {
    ...Typography.titleLarge,
    fontSize: 32,
    fontWeight: '700',
  },
  riskBar: {
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  riskBarFill: {
    height: '100%',
    borderRadius: 4,
  },
  threatTypeSection: {
    gap: 8,
  },
  sectionLabel: {
    ...Typography.labelMedium,
    fontSize: 14,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    gap: 6,
    alignSelf: 'flex-start',
  },
  categoryChipText: {
    ...Typography.labelSmall,
    fontSize: 12,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  industriesSection: {
    gap: 8,
  },
  industriesList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  industryChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  industryChipText: {
    ...Typography.labelSmall,
    fontSize: 12,
  },
  recommendationsSection: {
    gap: 8,
  },
  recommendationItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    paddingVertical: 4,
  },
  recommendationText: {
    ...Typography.bodySmall,
    fontSize: 14,
    flex: 1,
    lineHeight: 20,
  },
  summaryCard: {
    borderRadius: 20,
    padding: 0,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 8,
    overflow: 'hidden',
  },
  summaryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    gap: 12,
  },
  aiIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  summaryHeaderText: {
    flex: 1,
    gap: 2,
  },
  summaryTitle: {
    ...Typography.titleLarge,
    fontSize: 20,
    fontWeight: '700',
    letterSpacing: 0.15,
  },
  summarySubtitle: {
    ...Typography.bodySmall,
    fontSize: 13,
    opacity: 0.8,
  },
  summaryDivider: {
    height: 1,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    marginHorizontal: 20,
  },
  summaryContent: {
    paddingHorizontal: 20,
    paddingVertical: 20,
  },
  summaryText: {
    ...Typography.bodyLarge,
    fontSize: 17,
    lineHeight: 26,
    letterSpacing: 0.1,
    textAlign: 'left',
  },
  summaryHighlight: {
    ...Typography.bodyLarge,
    fontSize: 17,
    lineHeight: 26,
    letterSpacing: 0.1,
    fontWeight: '700',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginBottom: 4,
    textAlign: 'left',
  },
  summaryFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    gap: 6,
  },
  summaryFooterText: {
    ...Typography.labelMedium,
    fontSize: 12,
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  ctaContainer: {
    alignItems: 'center',
  },
  ctaButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
    gap: 8,
  },
  ctaButtonText: {
    ...Typography.labelLarge,
    fontSize: 16,
    fontWeight: '600',
  },
});