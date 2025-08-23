"use client"

import React, { useState } from "react"
import { View, Text, TouchableOpacity, Image, StyleSheet } from "react-native"
import { MaterialIcons } from "@expo/vector-icons"
import { useTheme } from "../../store/ThemeContext"
import { Colors } from "../../constants/Colors"
import { Typography } from "../../constants/Typography"
import type { Article } from "../../types/news"
import { formatDistanceToNow } from "../../utils/dateUtils"
import { generateConsistentRiskScore, getThreatLevel } from "../../utils/threatAnalysis"
import { putTempArticle } from "../../utils/tempArticleStore"
import { SimpleWebViewModal } from "./SimpleWebViewModal"
import { useReactions } from "../../store/LikeDislikeContext"

interface SearchResultItemProps {
  article: Article
  onPress?: () => void
}

export const SearchResultItem: React.FC<SearchResultItemProps> = ({ article }) => {
  const { resolvedTheme } = useTheme()
  const colors = Colors[resolvedTheme]
  const [modalVisible, setModalVisible] = useState(false)
  const { getReaction, toggleLike, toggleDislike } = useReactions()
  const reaction = getReaction(article.url) || {
    liked: false,
    disliked: false,
    likeCount: Math.floor(Math.random() * 40) + 5,
    updatedAt: 0,
  }

  // Derive consistent risk & level for Google articles
  const riskScore = generateConsistentRiskScore(article as any)
  const threatLevel = getThreatLevel(article as any)
  const threatColor = (() => {
    switch (threatLevel) {
      case "critical":
        return colors.critical || "#DC2626"
      case "high":
        return colors.vulnerability || "#EF4444"
      case "medium":
        return colors.threat || "#F59E0B"
      case "low":
        return colors.security || "#10B981"
      default:
        return colors.security || "#10B981"
    }
  })()

  const getThreatLevelIcon = (level?: string) => {
    switch (level) {
      case "critical":
        return "warning"
      case "high":
        return "error"
      case "medium":
        return "info"
      case "low":
        return "check-circle"
      default:
        return "article"
    }
  }

  const handlePress = React.useCallback(() => {
    // Store article in temp storage for potential use
    putTempArticle(article)

    // Show modal with beautiful animation
    setModalVisible(true)
  }, [article])

  const timeAgo = formatDistanceToNow(new Date(article.publishedAt))

  // Strip HTML tags from Google RSS description
  const cleanDescription = article.description
    ? article.description
        .replace(/<[^>]+>/g, "")
        .replace(/\*\*(.*?)\*\*/g, "$1")
        .replace(/&nbsp;/g, " ")
        .trim()
    : ""

  return (
    <>
      <TouchableOpacity
        style={[styles.container, { backgroundColor: colors.surface, borderColor: colors.cardBorder }]}
        onPress={handlePress}
        activeOpacity={0.85}
      >
        <View style={styles.content}>
          {/* Top row: source + time + risk */}
          <View style={styles.topRow}>
            <View style={styles.sourceGroup}>
              <MaterialIcons name="article" size={14} color={colors.primary} />
              <Text style={[styles.sourceName, { color: colors.primary }]} numberOfLines={1}>
                {article.source.name}
              </Text>
              <View style={[styles.levelBadge, { backgroundColor: threatColor + "20", borderColor: threatColor }]}>
                <MaterialIcons name={getThreatLevelIcon(threatLevel) as any} size={10} color={threatColor} />
                <Text style={[styles.levelText, { color: threatColor }]}>{threatLevel.toUpperCase()}</Text>
              </View>
              <View style={styles.riskChip}>
                <MaterialIcons
                  name={riskScore >= 80 ? "warning" : riskScore >= 60 ? "error" : "info"}
                  size={10}
                  color={riskScore >= 80 ? "#FF6B35" : riskScore >= 60 ? "#FFD93D" : colors.primary}
                />
                <Text
                  style={[
                    styles.riskText,
                    { color: riskScore >= 80 ? "#FF6B35" : riskScore >= 60 ? "#FFD93D" : colors.primary },
                  ]}
                >
                  {riskScore}%
                </Text>
              </View>
            </View>
            <Text style={[styles.timeAgo, { color: colors.textSecondary }]}>{timeAgo}</Text>
          </View>

          {/* Main content */}
          <View style={styles.mainContent}>
            <View style={styles.textContent}>
              <Text style={[styles.title, { color: colors.text }]} numberOfLines={3}>
                {article.title}
              </Text>

              {cleanDescription.length > 0 && (
                <Text style={[styles.description, { color: colors.textSecondary }]} numberOfLines={2}>
                  {cleanDescription}
                </Text>
              )}

              {/* Categories & Sectors (dedup + single row) */}
              {(article.categories?.length || article.affectedSectors?.length) && (
                <View style={styles.categoriesContainer}>
                  {Array.from(new Set(article.categories || []))
                    .slice(0, 2)
                    .map((category, idx) => (
                      <View key={`c-${idx}`} style={[styles.categoryTag, { backgroundColor: colors.primary + "20" }]}>
                        <Text style={[styles.categoryText, { color: colors.primary }]}>
                          {category.replace("-", " ")}
                        </Text>
                      </View>
                    ))}
                  {article.affectedSectors &&
                    Array.from(new Set(article.affectedSectors))
                      .slice(0, 2)
                      .map((sec, idx) => (
                        <View
                          key={`s-${idx}`}
                          style={[styles.categoryTag, { backgroundColor: colors.security + "20" }]}
                        >
                          <Text style={[styles.categoryText, { color: colors.security }]}>{sec.replace("-", " ")}</Text>
                        </View>
                      ))}
                  {((article.categories?.length || 0) > 2 || (article.affectedSectors?.length || 0) > 2) && (
                    <Text style={[styles.moreCategories, { color: colors.textSecondary }]}>
                      +
                      {((article.categories?.length || 0) - 2 > 0 ? article.categories!.length - 2 : 0) +
                        ((article.affectedSectors?.length || 0) - 2 > 0 ? article.affectedSectors!.length - 2 : 0)}{" "}
                      more
                    </Text>
                  )}
                </View>
              )}
            </View>

            {/* Thumbnail */}
            {article.urlToImage && (
              <View style={styles.imageContainer}>
                <Image source={{ uri: article.urlToImage }} style={styles.thumbnail} resizeMode="cover" />
              </View>
            )}
          </View>
          <View style={styles.bottomRow}>
            <View style={styles.inlineActions}>
              <TouchableOpacity
                style={[styles.likeBtn, reaction.liked && { backgroundColor: colors.primary + "22" }]}
                onPress={() => toggleLike(article)}
              >
                <MaterialIcons
                  name={reaction.liked ? "thumb-up" : "thumb-up-off-alt"}
                  size={14}
                  color={reaction.liked ? colors.primary : colors.textSecondary}
                />
                <Text style={[styles.likeCount, { color: reaction.liked ? colors.primary : colors.textSecondary }]}>
                  {reaction.likeCount}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.likeBtn, reaction.disliked && { backgroundColor: colors.error + "22" }]}
                onPress={() => toggleDislike(article)}
              >
                <MaterialIcons
                  name={reaction.disliked ? "thumb-down" : "thumb-down-off-alt"}
                  size={14}
                  color={reaction.disliked ? colors.error : colors.textSecondary}
                />
              </TouchableOpacity>
              <MaterialIcons name="open-in-new" size={16} color={colors.textSecondary} />
            </View>
          </View>
        </View>
      </TouchableOpacity>

      {/* Conditional modal rendering to prevent useInsertionEffect warnings */}
      {modalVisible && (
        <SimpleWebViewModal visible={modalVisible} url={article.url} onClose={() => setModalVisible(false)} />
      )}
    </>
  )
}

const styles = StyleSheet.create({
  container: { marginVertical: 8, marginHorizontal: 8, borderRadius: 16, borderWidth: 1, overflow: "hidden" },
  content: {
    padding: 14,
  },
  topRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 },
  sourceGroup: { flexDirection: "row", alignItems: "center", gap: 6, flexShrink: 1 },
  sourceInfo: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
    gap: 8,
  },
  sourceName: {
    ...Typography.caption,
    fontSize: 12,
    fontWeight: "600",
  },
  levelBadge: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    borderWidth: 1,
  },
  levelText: { ...Typography.caption, fontSize: 10, fontWeight: "700" },
  riskChip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    backgroundColor: "rgba(0,0,0,0.05)",
  },
  riskText: { ...Typography.caption, fontSize: 10, fontWeight: "600" },
  timeAgo: {
    ...Typography.caption,
    fontSize: 11,
  },
  mainContent: {
    flexDirection: "row",
    gap: 12,
    marginBottom: 12,
  },
  textContent: {
    flex: 1,
  },
  title: {
    ...Typography.subtitle,
    fontSize: 15,
    fontWeight: "600",
    lineHeight: 21,
    marginBottom: 4,
  },
  description: {
    ...Typography.body,
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 8,
  },
  categoriesContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    alignItems: "center",
    gap: 6,
  },
  categoryTag: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  categoryText: {
    ...Typography.caption,
    fontSize: 11,
    fontWeight: "500",
    textTransform: "capitalize",
  },
  moreCategories: {
    ...Typography.caption,
    fontSize: 11,
    fontStyle: "italic",
  },
  imageContainer: {
    width: 80,
    height: 80,
  },
  thumbnail: {
    width: "100%",
    height: "100%",
    borderRadius: 8,
  },
  bottomRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginTop: -4 },
  tagRow: { flexDirection: "row", flexWrap: "wrap", gap: 6, maxWidth: "85%" },
  inlineActions: { flexDirection: "row", alignItems: "center", gap: 12 },
  likeBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 6,
    paddingVertical: 4,
    borderRadius: 12,
  },
  likeCount: { ...Typography.labelSmall, fontSize: 11, fontWeight: "600" },
})
