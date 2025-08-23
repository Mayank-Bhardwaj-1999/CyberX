import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import { MaterialIcons } from '@expo/vector-icons';
import { useReactions } from '../../store/LikeDislikeContext';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';
import { BookmarkButton } from '../BookmarkButton';
import { formatRelativeTime } from '../../utils/dateUtils';
import { generateConsistentRiskScore, getThreatLevel, getThreatLevelColor } from '../../utils/threatAnalysis';
import { OptimizedImage } from './OptimizedImage';
import type { Article } from '../../types/news';

interface ModernNewsCardProps {
  article: Article;
  onPress: () => void;
  viewMode?: 'default' | 'compact' | 'list';
}

export function ModernNewsCard({ article, onPress, viewMode = 'default' }: ModernNewsCardProps) {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme] || Colors.dark;
  const { getReaction, toggleLike, toggleDislike } = useReactions();
  const reaction = getReaction(article.url) || { liked: false, disliked: false, likeCount: Math.floor(Math.random()*40)+10, updatedAt: 0 };

  // Get consistent threat analysis for this article
  const riskScore = generateConsistentRiskScore(article);
  const threatLevel = getThreatLevel(article);
  const threatColor = getThreatLevelColor(threatLevel, colors);

  const getSourceIcon = (sourceName: string) => {
    const name = sourceName.toLowerCase();
    if (name.includes('bleeping')) return 'security';
    if (name.includes('threat')) return 'warning';
    if (name.includes('hack')) return 'bug-report';
    if (name.includes('malware')) return 'security';
    if (name.includes('breach')) return 'shield';
    return 'article';
  };

  const getSourceColor = (sourceName: string) => {
    const name = sourceName.toLowerCase();
    if (name.includes('bleeping')) return '#00D4AA';
    if (name.includes('threat')) return '#FF6B35';
    if (name.includes('hack')) return '#FFD93D';
    if (name.includes('malware')) return '#FF6B35';
    if (name.includes('breach')) return '#E74C3C';
    return colors.primary;
  };

  const sourceIcon = getSourceIcon(article.source.name);
  const sourceColor = getSourceColor(article.source.name);

  // Compact view for 2-column grid layout (list-style within grid)
  if (viewMode === 'compact') {
    return (
      <TouchableOpacity 
        style={[styles.compactListItem, { backgroundColor: colors.surface, borderColor: colors.outline }]}
        onPress={onPress}
        activeOpacity={0.7}
      >
        {/* Left: Small Image */}
        <View style={styles.compactListImage}>
          {article.urlToImage ? (
            <OptimizedImage
              source={article.urlToImage}
              style={styles.compactListImg}
              placeholder="LKO2?V%2Tw=w]~RBVZRi};RPxuwH"
            />
          ) : (
            <View style={[styles.compactListPlaceholder, { backgroundColor: colors.cardBorder }]}>
              <MaterialIcons name="security" size={16} color={colors.textSecondary} />
            </View>
          )}
          
          {/* Small Threat Badge */}
          <View style={[styles.compactListThreatBadge, { backgroundColor: threatColor }]}>
            <MaterialIcons 
              name={threatLevel === 'critical' ? 'warning' : threatLevel === 'high' ? 'error' : 'info'} 
              size={8} 
              color="#FFFFFF" 
            />
          </View>
        </View>

        {/* Right: Content */}
        <View style={styles.compactListContent}>
          {/* Title */}
          <Text style={[styles.compactListTitle, { color: colors.text }]} numberOfLines={2}>
            {article.title}
          </Text>
          
          {/* Source and Time */}
          <View style={styles.compactListMeta}>
            <Text style={[styles.compactListSource, { color: colors.textSecondary }]} numberOfLines={1}>
              {article.source.name}
            </Text>
            <Text style={[styles.compactListTime, { color: colors.textSecondary }]}>
              {formatRelativeTime(article.publishedAt)}
            </Text>
          </View>
          
          {/* Risk Score */}
          <View style={styles.compactListRisk}>
            <MaterialIcons 
              name={riskScore >= 80 ? 'warning' : riskScore >= 60 ? 'error' : 'info'} 
              size={12} 
              color={riskScore >= 80 ? '#FF6B35' : riskScore >= 60 ? '#FFD93D' : colors.primary} 
            />
            <Text style={[styles.compactListRiskText, { 
              color: riskScore >= 80 ? '#FF6B35' : riskScore >= 60 ? '#FFD93D' : colors.primary 
            }]}>
              {riskScore}%
            </Text>
          </View>
        </View>

        {/* Bookmark Button */}
        <View style={styles.compactListBookmark}>
          <BookmarkButton article={article} />
        </View>
      </TouchableOpacity>
    );
  }

  // List view for single column layout
  if (viewMode === 'list') {
    return (
      <TouchableOpacity 
        style={[styles.listItem, { backgroundColor: colors.surface, borderColor: colors.outline }]}
        onPress={onPress}
        activeOpacity={0.7}
      >
        {/* Left: Medium Image */}
        <View style={styles.listImage}>
          {article.urlToImage ? (
            <OptimizedImage
              source={article.urlToImage}
              style={styles.listImg}
              placeholder="LKO2?V%2Tw=w]~RBVZRi};RPxuwH"
            />
          ) : (
            <View style={[styles.listPlaceholder, { backgroundColor: colors.cardBorder }]}>
              <MaterialIcons name="security" size={24} color={colors.textSecondary} />
            </View>
          )}
          
          {/* Threat Badge */}
          <View style={[styles.listThreatBadge, { backgroundColor: threatColor }]}>
            <MaterialIcons 
              name={threatLevel === 'critical' ? 'warning' : threatLevel === 'high' ? 'error' : 'info'} 
              size={12} 
              color="#FFFFFF" 
            />
          </View>
        </View>

        {/* Right: Content */}
        <View style={styles.listContent}>
          {/* Title */}
          <Text style={[styles.listTitle, { color: colors.text }]} numberOfLines={3}>
            {article.title}
          </Text>
          
          {/* Description */}
          {article.description && (
            <Text style={[styles.listDescription, { color: colors.textSecondary }]} numberOfLines={2}>
              {article.description}
            </Text>
          )}
          
          {/* Meta Info */}
          <View style={styles.listMeta}>
            <View style={styles.listSourceTime}>
              <Text style={[styles.listSource, { color: colors.textSecondary }]} numberOfLines={1}>
                {article.source.name}
              </Text>
              <Text style={[styles.listTime, { color: colors.textSecondary }]}>
                {formatRelativeTime(article.publishedAt)}
              </Text>
            </View>
            
            {/* Risk Score */}
            <View style={styles.listRisk}>
              <MaterialIcons 
                name={riskScore >= 80 ? 'warning' : riskScore >= 60 ? 'error' : 'info'} 
                size={14} 
                color={riskScore >= 80 ? '#FF6B35' : riskScore >= 60 ? '#FFD93D' : colors.primary} 
              />
              <Text style={[styles.listRiskText, { 
                color: riskScore >= 80 ? '#FF6B35' : riskScore >= 60 ? '#FFD93D' : colors.primary 
              }]}>
                {riskScore}%
              </Text>
            </View>
          </View>
        </View>

        {/* Bookmark Button */}
        <View style={styles.listBookmark}>
          <BookmarkButton article={article} />
        </View>
      </TouchableOpacity>
    );
  }

  // Default view (existing layout)
  return (
    <TouchableOpacity
      style={[styles.container, { backgroundColor: colors.surface }]}
      onPress={onPress}
      activeOpacity={0.95}
    >
      {/* Hero Image Section */}
      <View style={styles.imageContainer}>
        {article.urlToImage ? (
          <OptimizedImage
            source={article.urlToImage}
            style={styles.heroImage}
            placeholder="LKO2?V%2Tw=w]~RBVZRi};RPxuwH"
          />
        ) : (
          <View style={[styles.placeholderImage, { backgroundColor: colors.cardBorder }]}>
            <MaterialIcons name="security" size={32} color={colors.textSecondary} />
          </View>
        )}

        {/* Source Badge */}
        <View style={[styles.sourceBadge, { backgroundColor: sourceColor }]}>
          <MaterialIcons name={sourceIcon} size={14} color="#FFFFFF" />
          <Text style={styles.sourceText}>{article.source.name}</Text>
        </View>

        {/* Threat Level Badge */}
        <View style={[styles.threatBadge, { backgroundColor: threatColor }]}>
          <MaterialIcons name={threatLevel === 'critical' ? 'warning' : threatLevel === 'high' ? 'error' : 'info'} size={12} color="#FFFFFF" />
          <Text style={styles.threatText}>{threatLevel.toUpperCase()}</Text>
        </View>

        {/* AI Summary Indicator */}
        {article.summary && (
          <View style={[styles.aiBadge, { backgroundColor: colors.primary }]}>
            <MaterialIcons name="auto-awesome" size={12} color="#FFFFFF" />
            <Text style={styles.aiText}>AI</Text>
          </View>
        )}
      </View>

      {/* Content Section */}
      <View style={styles.contentContainer}>
        {/* Title */}
        <Text style={[styles.title, { color: colors.text }]} numberOfLines={2}>
          {article.title}
        </Text>

        {/* Description/Summary */}
        <Text style={[styles.description, { color: colors.textSecondary }]} numberOfLines={3}>
          {(article.summary || article.description || '').replace(/\*\*(.*?)\*\*/g,'$1')}
        </Text>

        {/* Threat Summary */}
        <View style={styles.threatSummary}>
          <MaterialIcons name="psychology" size={16} color={colors.primary} />
          <Text style={[styles.threatSummaryText, { color: colors.textSecondary }]}>
            Risk Score: {riskScore}% • AI Analyzed
          </Text>
        </View>

        {/* Metadata */}
        <View style={styles.metadataContainer}>
          <View style={styles.metadataLeft}>
            <View style={styles.timeContainer}>
              <MaterialIcons name="schedule" size={14} color={colors.textSecondary} />
              <Text style={[styles.time, { color: colors.textSecondary }]}>
                {formatRelativeTime(article.publishedAt)}
              </Text>
            </View>
            
            <View style={styles.riskScoreContainer}>
              <MaterialIcons 
                name={riskScore >= 80 ? 'warning' : riskScore >= 60 ? 'error' : 'info'} 
                size={14} 
                color={riskScore >= 80 ? '#FF6B35' : riskScore >= 60 ? '#FFD93D' : colors.primary} 
              />
              <Text style={[styles.riskScore, { 
                color: riskScore >= 80 ? '#FF6B35' : riskScore >= 60 ? '#FFD93D' : colors.primary 
              }]}>
                {riskScore}%
              </Text>
            </View>
          </View>

          <View style={styles.actionButtons}>
            {/* Like Button */}
            <TouchableOpacity
              style={[styles.reactionButton, reaction.liked && { backgroundColor: colors.primary + '22' }]}
              onPress={() => toggleLike(article)}
              activeOpacity={0.7}
            >
              <MaterialIcons name={reaction.liked ? 'thumb-up' : 'thumb-up-off-alt'} size={16} color={reaction.liked ? colors.primary : colors.textSecondary} />
              <Text style={[styles.reactionCount, { color: reaction.liked ? colors.primary : colors.textSecondary }]}>{reaction.likeCount}</Text>
            </TouchableOpacity>
            {/* Dislike */}
            <TouchableOpacity
              style={[styles.reactionButton, reaction.disliked && { backgroundColor: colors.error + '22' }]}
              onPress={() => toggleDislike(article)}
              activeOpacity={0.7}
            >
              <MaterialIcons name={reaction.disliked ? 'thumb-down' : 'thumb-down-off-alt'} size={16} color={reaction.disliked ? colors.error : colors.textSecondary} />
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionButton, { backgroundColor: colors.primaryContainer }]}
              onPress={() => {/* share placeholder */}}
              activeOpacity={0.8}
            >
              <MaterialIcons name="share" size={16} color={colors.onPrimaryContainer} />
            </TouchableOpacity>
            <BookmarkButton article={article} />
          </View>
        </View>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  container: {
    marginHorizontal: 16,
    marginVertical: 8,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 6,
  },
  imageContainer: {
    height: 200,
    position: 'relative',
  overflow:'hidden',
  borderTopLeftRadius:16,
  borderTopRightRadius:16,
  },
  heroImage: {
    width: '100%',
    height: '100%',
  borderTopLeftRadius:16,
  borderTopRightRadius:16,
  },
  placeholderImage: {
    width: '100%',
    height: '100%',
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
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 3,
    elevation: 3,
  },
  sourceText: {
    ...Typography.labelSmall,
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 11,
  },
  threatBadge: {
    position: 'absolute',
    top: 12,
    right: 12,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 3,
    elevation: 3,
  },
  threatText: {
    ...Typography.labelSmall,
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 10,
  },
  aiBadge: {
    position: 'absolute',
    bottom: 12,
    right: 12,
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 3,
    elevation: 3,
  },
  aiText: {
    ...Typography.labelSmall,
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 9,
  },
  contentContainer: {
    padding: 16,
  },
  title: {
    ...Typography.headlineSmall,
    fontWeight: '700',
    lineHeight: 24,
    marginBottom: 8,
  },
  description: {
    ...Typography.bodyMedium,
    lineHeight: 20,
    marginBottom: 8,
  },
  threatSummary: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginBottom: 12,
  },
  threatSummaryText: {
    ...Typography.labelSmall,
    fontSize: 12,
  },
  metadataContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  metadataLeft: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  timeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  time: {
    ...Typography.labelSmall,
    fontSize: 12,
  },
  riskScoreContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  riskScore: {
    ...Typography.labelSmall,
    fontSize: 12,
    fontWeight: '600',
  },
  actionButtons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  reactionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 16,
  },
  reactionCount: {
    ...Typography.labelSmall,
    fontSize: 11,
    fontWeight: '600',
  },
  actionButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
  },
  // Compact view styles (original beautiful design)
  compactCard: {
    width: '48%',
    marginBottom: 16,
    borderRadius: 12,
    overflow: 'hidden',
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  compactImageContainer: {
    height: 120,
    position: 'relative',
  },
  compactImage: {
    width: '100%',
    height: '100%',
  },
  compactPlaceholder: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  compactThreatBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
  },
  compactContentContainer: {
    padding: 12,
    flex: 1,
  },
  compactTitle: {
    ...Typography.titleSmall,
    fontSize: 14,
    fontWeight: '600',
    lineHeight: 18,
    marginBottom: 8,
  },
  compactSource: {
    ...Typography.labelSmall,
    fontSize: 11,
    fontWeight: '500',
    marginBottom: 4,
  },
  compactTime: {
    ...Typography.labelSmall,
    fontSize: 10,
  },
  compactBookmark: {
    position: 'absolute',
    bottom: 8,
    right: 8,
  },
  // Legacy styles (keeping for compatibility)
  compactSourceBadge: {
    position: 'absolute',
    top: 8,
    left: 8,
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 3,
    elevation: 3,
  },
  compactSourceText: {
    ...Typography.labelSmall,
    color: '#FFFFFF',
    fontWeight: '600',
    fontSize: 9,
  },
  compactThreatText: {
    ...Typography.labelSmall,
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 8,
  },
  compactAiBadge: {
    position: 'absolute',
    bottom: 8,
    right: 8,
    paddingHorizontal: 4,
    paddingVertical: 2,
    borderRadius: 6,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 3,
    elevation: 3,
  },
  compactAiText: {
    ...Typography.labelSmall,
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 8,
  },
  compactDescription: {
    ...Typography.bodySmall,
    fontSize: 11,
    lineHeight: 14,
    marginBottom: 6,
  },
  compactThreatSummary: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
    marginBottom: 8,
  },
  compactThreatSummaryText: {
    ...Typography.labelSmall,
    fontSize: 10,
  },
  compactMetadataContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  compactTimeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  compactRiskContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  compactRiskScore: {
    ...Typography.labelSmall,
    fontSize: 10,
    fontWeight: '600',
  },
  compactActionButtons: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  compactActionButton: {
    width: 28,
    height: 28,
    borderRadius: 14,
    justifyContent: 'center',
    alignItems: 'center',
  },
  compactContent: {
    padding: 12,
    flex: 1,
  },
  compactMeta: {
    gap: 4,
  },
  // List-style compact view styles
  compactListItem: {
    width: '48%',
    marginBottom: 8,
    padding: 8,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  compactListImage: {
    width: 50,
    height: 50,
    position: 'relative',
  },
  compactListImg: {
    width: '100%',
    height: '100%',
    borderRadius: 6,
  },
  compactListPlaceholder: {
    width: '100%',
    height: '100%',
    borderRadius: 6,
    justifyContent: 'center',
    alignItems: 'center',
  },
  compactListThreatBadge: {
    position: 'absolute',
    top: -2,
    right: -2,
    width: 16,
    height: 16,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  compactListContent: {
    flex: 1,
    gap: 2,
  },
  compactListTitle: {
    ...Typography.titleSmall,
    fontSize: 12,
    fontWeight: '600',
    lineHeight: 14,
  },
  compactListMeta: {
    gap: 1,
  },
  compactListSource: {
    ...Typography.labelSmall,
    fontSize: 10,
    fontWeight: '500',
  },
  compactListTime: {
    ...Typography.labelSmall,
    fontSize: 9,
  },
  compactListRisk: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 2,
    marginTop: 2,
  },
  compactListRiskText: {
    ...Typography.labelSmall,
    fontSize: 9,
    fontWeight: '600',
  },
  compactListBookmark: {
    alignSelf: 'flex-start',
  },
  // List view styles (single column)
  listItem: {
    width: '100%',
    marginBottom: 12,
    padding: 12,
    borderRadius: 12,
    borderWidth: 1,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
  },
  listImage: {
    width: 80,
    height: 80,
    position: 'relative',
  },
  listImg: {
    width: '100%',
    height: '100%',
    borderRadius: 8,
  },
  listPlaceholder: {
    width: '100%',
    height: '100%',
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listThreatBadge: {
    position: 'absolute',
    top: -4,
    right: -4,
    width: 20,
    height: 20,
    borderRadius: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    flex: 1,
    gap: 6,
  },
  listTitle: {
    ...Typography.titleMedium,
    fontSize: 15,
    fontWeight: '600',
    lineHeight: 20,
  },
  listDescription: {
    ...Typography.bodyMedium,
    fontSize: 13,
    lineHeight: 18,
    marginTop: 4,
  },
  listMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  listSourceTime: {
    gap: 2,
    flex: 1,
  },
  listSource: {
    ...Typography.labelMedium,
    fontSize: 12,
    fontWeight: '500',
  },
  listTime: {
    ...Typography.labelSmall,
    fontSize: 11,
  },
  listRisk: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  listRiskText: {
    ...Typography.labelMedium,
    fontSize: 12,
    fontWeight: '600',
  },
  listBookmark: {
    alignSelf: 'flex-start',
    marginTop: 4,
  },
});
