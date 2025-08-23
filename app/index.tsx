import { useEffect, useState } from "react"
import { useRouter } from "expo-router"
import { View, Text, StyleSheet } from "react-native"
import { LinearGradient } from "expo-linear-gradient"
import { Feather } from "@expo/vector-icons"
import { useTheme } from "../store/ThemeContext"
import { Colors } from "../constants/Colors"
import { Typography } from "../constants/Typography"
import { MaterialElevation } from "../components/ui/MaterialComponents"

export default function Index() {
  const router = useRouter()
  const { resolvedTheme } = useTheme()
  const colors = Colors[resolvedTheme]
  const [connectionStatus, setConnectionStatus] = useState<'testing' | 'success' | 'failed'>('testing')
  const [loadingProgress, setLoadingProgress] = useState(0)

  useEffect(() => {
    // Simulate loading progress
    const progressInterval = setInterval(() => {
      setLoadingProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval)
          return 100
        }
        return prev + 10
      })
    }, 200)
    
    // Test API connection
    const testConnection = async () => {
      try {
        setConnectionStatus('testing')
        const response = await fetch(`${process.env.EXPO_PUBLIC_API_URL}/api/news?limit=1`, {
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true'
          }
        })
        
        if (response.ok) {
          await response.json() // Just consume the response
          setConnectionStatus('success')
        } else {
          setConnectionStatus('failed')
        }
      } catch (error) {
        setConnectionStatus('failed')
        setConnectionStatus('failed')
      }
    }

    testConnection()

    // Navigation with enhanced timing
    const timer = setTimeout(() => {
      try {
        router.replace("/(tabs)/news")
      } catch (error) {
        router.push("/(tabs)/news")
      }
    }, 3500)

    return () => {
      clearTimeout(timer)
      clearInterval(progressInterval)
    }
  }, [router])

  const getStatusMessage = () => {
    switch (connectionStatus) {
      case 'testing':
        return 'Establishing secure connection...'
      case 'success':
        return 'Connection secured! Loading latest threats...'
      case 'failed':
        return 'Offline mode enabled'
      default:
        return 'Initializing CyberX...'
    }
  }

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'testing':
        return 'wifi'
      case 'success':
        return 'shield'
      case 'failed':
        return 'wifi-off'
      default:
        return 'loader'
    }
  }

  return (
    <LinearGradient
      colors={[colors.primary, colors.secondary]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={styles.container}
    >
      <View style={styles.content}>
        {/* App Logo/Icon */}
        <MaterialElevation level={3} style={[styles.logoContainer, { backgroundColor: colors.surface }]}>
          <Feather name="shield" size={48} color={colors.primary} />
        </MaterialElevation>
        
        {/* App Title */}
        <Text style={[Typography.displaySmall, { color: colors.onPrimary, marginTop: 24 }]}>
          CyberX
        </Text>
        <Text style={[Typography.titleMedium, { color: colors.onPrimary, opacity: 0.9, marginTop: 8 }]}>
          Cybersecurity Intelligence Hub
        </Text>

        {/* Status Section */}
        <View style={styles.statusSection}>
          <MaterialElevation level={1} style={[styles.statusContainer, { backgroundColor: colors.surfaceContainer }]}>
            <View style={styles.statusIcon}>
              <Feather 
                name={getStatusIcon()} 
                size={24} 
                color={connectionStatus === 'success' ? colors.success : 
                       connectionStatus === 'failed' ? colors.warning : colors.primary} 
              />
            </View>
            <Text style={[Typography.bodyLarge, { color: colors.text, textAlign: 'center' }]}>
              {getStatusMessage()}
            </Text>
          </MaterialElevation>

          {/* Progress Bar */}
          <View style={[styles.progressContainer, { backgroundColor: colors.surfaceVariant }]}>
            <View 
              style={[
                styles.progressBar, 
                { 
                  backgroundColor: colors.primary,
                  width: `${loadingProgress}%`
                }
              ]} 
            />
          </View>
          
          <Text style={[Typography.labelMedium, { color: colors.onPrimary, opacity: 0.8, marginTop: 16 }]}>
            {loadingProgress}% Complete
          </Text>
        </View>

        {/* Security Badge */}
        <MaterialElevation level={2} style={[styles.securityBadge, { backgroundColor: colors.success }]}>
          <Feather name="lock" size={16} color={colors.onPrimary} />
          <Text style={[Typography.labelSmall, { color: colors.onPrimary, marginLeft: 8 }]}>
            SECURE CONNECTION
          </Text>
        </MaterialElevation>
      </View>
    </LinearGradient>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  logoContainer: {
    width: 96,
    height: 96,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  statusSection: {
    marginTop: 48,
    width: '100%',
    maxWidth: 320,
    alignItems: 'center',
  },
  statusContainer: {
    padding: 20,
    borderRadius: 16,
    width: '100%',
    alignItems: 'center',
    marginBottom: 20,
  },
  statusIcon: {
    marginBottom: 12,
  },
  progressContainer: {
    height: 6,
    width: '100%',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    borderRadius: 3,
  },
  securityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginTop: 32,
  },
})
