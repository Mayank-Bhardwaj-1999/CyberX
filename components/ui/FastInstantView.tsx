import { useEffect, useRef, useState } from 'react'
import { View, ActivityIndicator, Text, StyleSheet } from 'react-native'
import { WebView } from 'react-native-webview'
import { useTheme } from '../../store/ThemeContext'
import { Colors } from '../../constants/Colors'
import type { Article } from '../../types/news'

interface FastInstantViewProps { article: Article }

export function FastInstantView({ article }: FastInstantViewProps) {
  const { resolvedTheme } = useTheme()
  const colors = Colors[resolvedTheme]
  const [loading, setLoading] = useState(true)
  const webRef = useRef<WebView>(null)

  return (
    <View style={{ flex: 1 }}>
      {loading && (
        <View style={styles.loading}> 
          <ActivityIndicator size="small" color={colors.primary} />
          <Text style={{ color: colors.textSecondary, marginTop: 8 }}>Optimizing…</Text>
        </View>
      )}
      <WebView
        ref={webRef}
        source={{ uri: `https://r.jina.ai/http://r.jina.ai/http://r.jina.ai/${encodeURIComponent(article.url)}` }}
        onLoadEnd={() => setLoading(false)}
        originWhitelist={["*"]}
        showsVerticalScrollIndicator={false}
        style={{ backgroundColor: colors.background }}
      />
    </View>
  )
}

const styles = StyleSheet.create({
  loading: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, alignItems: 'center', justifyContent: 'center', zIndex: 10 }
})
