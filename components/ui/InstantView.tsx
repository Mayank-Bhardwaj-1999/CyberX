import { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  StatusBar,
  Share,
} from 'react-native';
import { WebView } from 'react-native-webview';
import { MaterialIcons } from '@expo/vector-icons';
import * as WebBrowser from 'expo-web-browser';
import { useTheme } from '../../store/ThemeContext';
import { Colors } from '../../constants/Colors';
import { Typography } from '../../constants/Typography';
import type { Article } from '../../types/news';
import { ArticleReader } from './ArticleReader';
import { useReaderMode } from '../../store/ReaderModeContext';
import { storage } from '../../services/storage';

interface InstantViewProps {
  article: Article;
  onBack: () => void;
}

export function InstantView({ article, onBack }: InstantViewProps) {
  const { resolvedTheme } = useTheme();
  const colors = Colors[resolvedTheme];
  const webViewRef = useRef<WebView>(null);
  
  const [loading, setLoading] = useState(true);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [canGoBack, setCanGoBack] = useState(false);
  const [canGoForward, setCanGoForward] = useState(false);
  const [currentUrl, setCurrentUrl] = useState(article.url);
  const [fallback, setFallback] = useState(false);
  const [extracted, setExtracted] = useState<{title:string;image?:string;domain?:string;blocks:any[];word_count:number}|null>(null);
  const [extracting, setExtracting] = useState(false);

  const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || 'https://cyberx.icu';
  const { mode } = useReaderMode();
  const sessionStartRef = useRef(Date.now());

  const triggerExtraction = async () => {
    if (extracting || extracted) return;
    try {
      setExtracting(true);
      const resp = await fetch(`${API_BASE_URL}/api/extract`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({ url: article.url }) });
      if (!resp.ok) throw new Error('extract failed');
      const data = await resp.json();
      if (data.status === 'success') {
        setExtracted({
          title: data.meta.title,
            image: data.meta.image,
            domain: data.meta.domain,
            blocks: data.content.blocks,
            word_count: data.content.word_count
        });
      }
    } catch (e) {
      console.warn('Extraction failed', e);
    } finally {
      setExtracting(false);
    }
  };

  const handleShare = async () => {
    try {
      await Share.share({
        message: `${article.title}\n\n${currentUrl}`,
        title: article.title,
      });
    } catch (error) {
      console.error('Error sharing article:', error);
    }
  };

  const handleRefresh = () => {
    webViewRef.current?.reload();
  };

  const openInCustomTab = async () => {
    try {
      // Launch Chrome Custom Tab / SFSafariViewController with theming
      await WebBrowser.openBrowserAsync(article.url, {
        enableBarCollapsing: true,
        readerMode: false,
        toolbarColor: colors.surface,
        controlsColor: colors.primary,
        secondaryToolbarColor: colors.background,
        dismissButtonStyle: 'close',
        presentationStyle: WebBrowser.WebBrowserPresentationStyle.FULL_SCREEN,
        showTitle: true
      });
    } catch (e) {
      console.warn('Custom tab open failed', e);
    }
  };

  const handleGoBack = () => {
    if (canGoBack) {
      webViewRef.current?.goBack();
    }
  };

  const handleGoForward = () => {
    if (canGoForward) {
      webViewRef.current?.goForward();
    }
  };

  const handleNavigationStateChange = (navState: any) => {
    setCanGoBack(navState.canGoBack);
    setCanGoForward(navState.canGoForward);
    setCurrentUrl(navState.url);
  };

  const handleError = () => {
    // Switch to fallback reader
    setFallback(true);
    triggerExtraction();
  };

  // Apply reader mode preferences
  useEffect(() => {
    if (mode === 'reader' && !fallback) {
      setFallback(true);
      triggerExtraction();
    } else if (mode === 'customTab') {
      openInCustomTab();
    }
  }, [mode]);

  // Session tracking
  useEffect(() => {
    return () => {
      const duration = Date.now() - sessionStartRef.current;
      storage.addReadingSession(article.url, fallback ? 'reader' : 'webview', duration);
    };
  }, [fallback, article.url]);

  // Optimize WebView performance
  const optimizedUserAgent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1';
  
  const handleWebViewMessage = (event: any) => {
    const data = event.nativeEvent.data;
    if (data === 'ACCESS_DENIED') {
      setFallback(true);
      triggerExtraction();
    } else {
      console.log('WebView message:', data);
    }
  };

  if (fallback && extracted) {
    return (
      <SafeAreaView style={[styles.container,{ backgroundColor: colors.background }]}> 
        <StatusBar barStyle={resolvedTheme === 'dark' ? 'light-content':'dark-content'} backgroundColor={colors.surface} />
        <View style={[styles.header,{ backgroundColor: colors.surface }]}> 
          <View style={styles.headerLeft}> 
            <TouchableOpacity style={[styles.headerButton,{ backgroundColor: colors.background }]} onPress={onBack}> 
              <MaterialIcons name="close" size={24} color={colors.text} />
            </TouchableOpacity>
            <Text style={[styles.headerTitle,{ color: colors.text }]} numberOfLines={1}>Readable View</Text>
          </View>
          <View style={styles.headerRight}>
            <TouchableOpacity style={[styles.headerButton,{ backgroundColor: colors.background }]} onPress={handleShare}>
              <MaterialIcons name="share" size={20} color={colors.text} />
            </TouchableOpacity>
          </View>
        </View>
        {extracting && (
          <View style={[styles.loadingContainer,{ backgroundColor: colors.background }]}> 
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={[styles.loadingText,{ color: colors.textSecondary }]}>Extracting article...</Text>
          </View>
        )}
        <ArticleReader title={extracted.title} image={extracted.image} domain={extracted.domain} blocks={extracted.blocks} wordCount={extracted.word_count} />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar 
        barStyle={resolvedTheme === 'dark' ? 'light-content' : 'dark-content'} 
        backgroundColor={colors.surface} 
      />
      
      {/* Custom Header */}
      <View style={[styles.header, { backgroundColor: colors.surface }]}>
        <View style={styles.headerLeft}>
          <TouchableOpacity
            style={[styles.headerButton, { backgroundColor: colors.background }]}
            onPress={onBack}
          >
            <MaterialIcons name="close" size={24} color={colors.text} />
          </TouchableOpacity>
          
          <Text style={[styles.headerTitle, { color: colors.text }]} numberOfLines={1}>
            {fallback ? 'Instant View' : 'Instant View'}
          </Text>
        </View>

        <View style={styles.headerRight}>
          <TouchableOpacity
            style={[styles.headerButton, { backgroundColor: colors.background }]}
            onPress={handleGoBack}
            disabled={!canGoBack}
          >
            <MaterialIcons 
              name="arrow-back" 
              size={20} 
              color={canGoBack ? colors.text : colors.textSecondary} 
            />
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.headerButton, { backgroundColor: colors.background }]}
            onPress={handleGoForward}
            disabled={!canGoForward}
          >
            <MaterialIcons 
              name="arrow-forward" 
              size={20} 
              color={canGoForward ? colors.text : colors.textSecondary} 
            />
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.headerButton, { backgroundColor: colors.background }]}
            onPress={handleRefresh}
          >
            <MaterialIcons name="refresh" size={20} color={colors.text} />
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.headerButton, { backgroundColor: colors.background }]}
            onPress={openInCustomTab}
          >
            <MaterialIcons name="open-in-browser" size={20} color={colors.text} />
          </TouchableOpacity>
          
          <TouchableOpacity
            style={[styles.headerButton, { backgroundColor: colors.background }]}
            onPress={handleShare}
          >
            <MaterialIcons name="share" size={20} color={colors.text} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Loading Indicator with Progress */}
      {loading && (
        <View style={[styles.loadingContainer, { backgroundColor: colors.background }]}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.loadingText, { color: colors.textSecondary }]}>
            Loading article...
          </Text>
          {loadingProgress > 0 && loadingProgress < 1 && (
            <View style={[styles.progressContainer, { backgroundColor: colors.cardBorder }]}>
              <View 
                style={[
                  styles.progressBar, 
                  { backgroundColor: colors.primary, width: `${loadingProgress * 100}%` }
                ]} 
              />
            </View>
          )}
        </View>
      )}

      {fallback && !extracted && (
        <View style={[styles.loadingContainer,{ backgroundColor: colors.background }]}> 
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={[styles.loadingText,{ color: colors.textSecondary }]}>Switching to readable view...</Text>
        </View>
      )}

      {!fallback && (
      <WebView
        ref={webViewRef}
        source={{ 
          uri: article.url,
          headers: {
            'User-Agent': optimizedUserAgent,
            'Cache-Control': 'max-age=3600',
            'Accept-Encoding': 'gzip, deflate',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
          }
        }}
        style={[styles.webView, { backgroundColor: colors.background }]}
        onLoadStart={() => {
          setLoading(true);
          setLoadingProgress(0);
        }}
        onLoadProgress={({ nativeEvent }) => {
          setLoadingProgress(nativeEvent.progress);
        }}
        onLoadEnd={() => {
          setLoading(false);
          setLoadingProgress(1);
        }}
        onError={handleError}
        onNavigationStateChange={handleNavigationStateChange}
        onMessage={handleWebViewMessage}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        startInLoadingState={false}
        originWhitelist={['*']}
        mixedContentMode="always"
        thirdPartyCookiesEnabled={true}
        cacheEnabled={true}
        cacheMode="LOAD_CACHE_ELSE_NETWORK"
        incognito={false}
        allowsFullscreenVideo={false}
        allowFileAccess={false}
        allowsLinkPreview={false}
        allowsBackForwardNavigationGestures={true}
        bounces={false}
        scalesPageToFit={false}
        showsHorizontalScrollIndicator={false}
        showsVerticalScrollIndicator={false}
        hideKeyboardAccessoryView={true}
        keyboardDisplayRequiresUserAction={false}
        allowsInlineMediaPlayback={false}
        mediaPlaybackRequiresUserAction={true}
        scrollEnabled={true}
        pullToRefreshEnabled={false}
        injectedJavaScript={`
          setTimeout(() => {
            const ads = document.querySelectorAll('[class*="ad"], [id*="ad"], .advertisement');
            ads.forEach(el => el.remove());
            const socialWidgets = document.querySelectorAll('[class*="social"], [class*="share"], [class*="comment"]');
            socialWidgets.forEach(el => el.remove());
            const images = document.querySelectorAll('img');
            images.forEach(img => { if (img.src && !img.src.includes('data:')) { img.loading = 'lazy'; } });
          }, 500);
          true;
        `}
      />)}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(0,0,0,0.1)',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  headerButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    ...Typography.titleMedium,
    fontSize: 18,
    fontWeight: '600',
    marginLeft: 12,
    flex: 1,
  },
  loadingContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 999,
  },
  loadingText: {
    ...Typography.bodyMedium,
    marginTop: 12,
    fontSize: 16,
  },
  webView: {
    flex: 1,
  },
  progressContainer: {
    width: '80%',
    height: 3,
    borderRadius: 2,
    marginTop: 16,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    borderRadius: 2,
  },
});
