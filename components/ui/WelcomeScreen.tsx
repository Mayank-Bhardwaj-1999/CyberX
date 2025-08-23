import React from "react"
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ImageBackground,
  StatusBar,
  Animated,
} from "react-native"
import { LinearGradient } from "expo-linear-gradient"
import { MaterialIcons } from "@expo/vector-icons"
import { Colors } from "../../constants/Colors"
import { Typography } from "../../constants/Typography"
import { useTheme } from "../../store/ThemeContext"

interface WelcomeScreenProps {
  onExplore: () => void
}

export function WelcomeScreen({ onExplore }: WelcomeScreenProps) {
  const { theme } = useTheme()
  const colors = Colors[theme === "auto" ? "light" : theme]
  const fadeAnim = new Animated.Value(0)
  const slideAnim = new Animated.Value(50)

  React.useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 800,
        useNativeDriver: true,
      }),
    ]).start()
  }, [])

  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <StatusBar barStyle={theme === "dark" ? "light-content" : "dark-content"} />

      <ImageBackground
        source={{
          uri: "https://images.unsplash.com/photo-1504711434969-e33886168f5c?w=800&auto=format&fit=crop&q=80",
        }}
        style={styles.heroContainer}
        resizeMode="cover"
      >
        <LinearGradient
          colors={["rgba(74, 108, 247, 0.8)", "rgba(124, 58, 237, 0.9)", "rgba(15, 15, 35, 0.95)"]}
          style={styles.gradient}
        />

        <Animated.View
          style={[
            styles.contentContainer,
            {
              opacity: fadeAnim,
              transform: [{ translateY: slideAnim }],
            },
          ]}
        >
          {/* Logo */}
          <View style={styles.logoContainer}>
            <View style={[styles.logoIcon, { backgroundColor: colors.primary }]}>
              <MaterialIcons name="article" size={32} color="#FFFFFF" />
            </View>
            <Text style={[styles.logoText, { color: "#FFFFFF" }]}>NewsHub</Text>
          </View>

          {/* Main Content */}
          <View style={styles.textContainer}>
            <Text style={[styles.title, { color: "#FFFFFF" }]}>
              Stay Informed with{"\n"}
              <Text style={{ color: colors.accent }}>Real-Time News</Text>
            </Text>

            <Text style={[styles.subtitle, { color: "rgba(255, 255, 255, 0.8)" }]}>
              Get the latest cybersecurity updates, breaking news, and expert insights from trusted sources worldwide.
            </Text>
          </View>

          {/* Features */}
          <View style={styles.featuresContainer}>
            <View style={styles.feature}>
              <MaterialIcons name="flash-on" size={24} color={colors.accent} />
              <Text style={[styles.featureText, { color: "#FFFFFF" }]}>Real-time Updates</Text>
            </View>
            <View style={styles.feature}>
              <MaterialIcons name="bookmark" size={24} color={colors.accent} />
              <Text style={[styles.featureText, { color: "#FFFFFF" }]}>Save for Later</Text>
            </View>
            <View style={styles.feature}>
              <MaterialIcons name="dark-mode" size={24} color={colors.accent} />
              <Text style={[styles.featureText, { color: "#FFFFFF" }]}>Dark Mode</Text>
            </View>
          </View>

          {/* CTA Button */}
          <TouchableOpacity
            style={[styles.exploreButton, { backgroundColor: colors.accent }]}
            onPress={onExplore}
            activeOpacity={0.8}
          >
            <Text style={[styles.buttonText, { color: "#FFFFFF" }]}>Start Reading</Text>
            <MaterialIcons name="arrow-forward" size={20} color="#FFFFFF" />
          </TouchableOpacity>
        </Animated.View>
      </ImageBackground>
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  heroContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  gradient: {
    position: "absolute",
    left: 0,
    right: 0,
    top: 0,
    bottom: 0,
  },
  contentContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 24,
    paddingVertical: 60,
  },
  logoContainer: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 40,
  },
  logoIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },
  logoText: {
    ...Typography.headlineMedium,
    fontSize: 28,
    fontWeight: "700",
  },
  textContainer: {
    alignItems: "center",
    marginBottom: 40,
  },
  title: {
    ...Typography.headlineLarge,
    fontSize: 36,
    textAlign: "center",
    marginBottom: 16,
    lineHeight: 44,
  },
  subtitle: {
    ...Typography.bodyLarge,
    textAlign: "center",
    lineHeight: 24,
    paddingHorizontal: 8,
  },
  featuresContainer: {
    flexDirection: "row",
    justifyContent: "space-around",
    width: "100%",
    marginBottom: 40,
  },
  feature: {
    alignItems: "center",
    gap: 8,
  },
  featureText: {
    ...Typography.caption,
    fontSize: 12,
    textAlign: "center",
  },
  exploreButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 28,
    minWidth: 180,
    gap: 8,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  buttonText: {
    ...Typography.button,
    fontSize: 16,
    fontWeight: "600",
  },
})
