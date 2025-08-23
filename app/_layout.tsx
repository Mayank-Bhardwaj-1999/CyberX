import { useEffect } from "react"
import { useFonts } from "expo-font"
import { SplashScreen, Stack } from "expo-router"
import { StatusBar } from "expo-status-bar"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { SafeAreaProvider } from "react-native-safe-area-context"
import { GestureHandlerRootView } from "react-native-gesture-handler"
import { ThemeProvider, useTheme } from "../store/ThemeContext"
import { NotificationProvider } from "../store/NotificationContext"
import { BookmarkProvider } from "../store/BookmarkContext"
import { NewsProvider } from "../store/NewsContext"
import { ReaderModeProvider } from "../store/ReaderModeContext"
import { PersonalFeedProvider } from "../store/PersonalFeedContext"
import { LikeDislikeProvider } from "../store/LikeDislikeContext"
import { initializeNotificationService } from "../services/notifications"
import { enhancedNotificationService } from "../services/enhancedNotifications"
import { feedPushNotificationService } from "../services/feedNotifications"
import { UpdateService } from "../services/updateService"
import { SimpleAnalyticsService } from "../services/simpleAnalytics"
import ErrorBoundary from "../components/ErrorBoundary"

// Prevent the splash screen from auto-hiding
SplashScreen.preventAutoHideAsync()

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
})

function StatusBarWrapper() {
  const { resolvedTheme } = useTheme();
  return (
    <StatusBar style={resolvedTheme === 'dark' ? 'light' : 'dark'} />
  );
}

export default function RootLayout() {
  const [loaded] = useFonts({
    "Inter-Regular": require("../assets/fonts/Inter-Regular.ttf"),
    "Inter-Medium": require("../assets/fonts/Inter-Medium.ttf"),
    "Inter-SemiBold": require("../assets/fonts/Inter-SemiBold.ttf"),
    "Inter-Bold": require("../assets/fonts/Inter-Bold.ttf"),
  })

  useEffect(() => {
    if (loaded) {
      SplashScreen.hideAsync()
      
      // Initialize Simple Analytics
      SimpleAnalyticsService.initialize().then(() => {
        console.log('📊 Analytics initialized successfully')
        SimpleAnalyticsService.trackAppOpen()
      }).catch((error) => {
        console.log('Analytics initialization failed, but app will continue normally')
      })
      
      // Initialize notification service
      initializeNotificationService().then((success) => {
        if (success) {
          console.log('🔔 Notifications initialized successfully')
        } else {
          console.log('❌ Failed to initialize notifications')
        }
      }).catch((error) => {
        console.error('Error initializing notifications:', error)
      })

      // Initialize enhanced notification service
      enhancedNotificationService.initialize().then(() => {
        console.log('🚀 Enhanced notifications initialized successfully')
      }).catch((error) => {
        console.error('Error initializing enhanced notifications:', error)
      })

      // Initialize feed push notification service
      feedPushNotificationService.initialize().then(() => {
        console.log('📰 Feed push notifications initialized successfully')
      }).catch((error) => {
        console.error('Error initializing feed notifications:', error)
      })

      // Check for critical updates on app launch
      UpdateService.checkForCriticalUpdates().then(() => {
        console.log('✅ Update check completed on startup')
      }).catch((error) => {
        console.error('Error checking for updates:', error)
      })
    }
  }, [loaded])

  if (!loaded) {
    return null
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ErrorBoundary>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <NotificationProvider>
              <BookmarkProvider>
                <NewsProvider>
                  <ReaderModeProvider>
                    <PersonalFeedProvider>
                      <LikeDislikeProvider>
                        <SafeAreaProvider>
                          <Stack screenOptions={{ headerShown: false }}>
                            <Stack.Screen name="index" options={{ headerShown: false }} />
                            <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
                            <Stack.Screen name="article-view/[id]" options={{ headerShown: false }} />
                            <Stack.Screen name="instant-view/[id]" options={{ headerShown: false }} />
                            <Stack.Screen name="web-view/[id]" options={{ headerShown: false }} />
                          </Stack>
                          <StatusBarWrapper />
                        </SafeAreaProvider>
                      </LikeDislikeProvider>
                    </PersonalFeedProvider>
                  </ReaderModeProvider>
                </NewsProvider>
              </BookmarkProvider>
            </NotificationProvider>
          </ThemeProvider>
        </QueryClientProvider>
      </ErrorBoundary>
    </GestureHandlerRootView>
  )
}
