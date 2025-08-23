import { Platform } from "react-native"

const fontFamily = {
  regular: Platform.select({
    ios: "SF Pro Display",
    android: "Inter-Regular",
    default: "System",
  }),
  medium: Platform.select({
    ios: "SF Pro Display",
    android: "Inter-Medium",
    default: "System",
  }),
  semiBold: Platform.select({
    ios: "SF Pro Display",
    android: "Inter-SemiBold",
    default: "System",
  }),
  bold: Platform.select({
    ios: "SF Pro Display",
    android: "Inter-Bold",
    default: "System",
  }),
}

const roundedFontFamily = Platform.select({
  ios: "SF Pro Rounded",
  android: "Inter-Bold",
  default: "System",
})

// Material Design 3 Type Scale - Enhanced Professional Typography System
export const Typography = {
  // Font families
  fontFamily,

  // Display styles - Largest text, reserved for short, important text or numerals
  displayLarge: {
    fontFamily: roundedFontFamily,
    fontSize: 57,
    fontWeight: "300" as const,
    lineHeight: 64,
    letterSpacing: -0.25,
  },
  displayMedium: {
    fontFamily: roundedFontFamily,
    fontSize: 45,
    fontWeight: "300" as const,
    lineHeight: 52,
    letterSpacing: 0,
  },
  displaySmall: {
    fontFamily: roundedFontFamily,
    fontSize: 36,
    fontWeight: "400" as const,
    lineHeight: 44,
    letterSpacing: 0,
  },

  // Headlines - High-emphasis text for short, impactful text
  headlineLarge: {
    fontFamily: fontFamily.bold,
    fontSize: 32,
    fontWeight: "700" as const,
    lineHeight: 40,
    letterSpacing: -0.5,
  },
  headlineMedium: {
    fontFamily: fontFamily.bold,
    fontSize: 28,
    fontWeight: "700" as const,
    lineHeight: 36,
    letterSpacing: -0.25,
  },
  headlineSmall: {
    fontFamily: fontFamily.semiBold,
    fontSize: 24,
    fontWeight: "600" as const,
    lineHeight: 32,
    letterSpacing: 0,
  },

  // Titles - For prominent titles and section headers
  titleLarge: {
    fontFamily: fontFamily.bold,
    fontSize: 22,
    fontWeight: "600" as const,
    lineHeight: 28,
    letterSpacing: 0,
  },
  titleMedium: {
    fontFamily: fontFamily.semiBold,
    fontSize: 20,
    fontWeight: "500" as const,
    lineHeight: 26,
    letterSpacing: 0.15,
  },
  titleSmall: {
    fontFamily: fontFamily.semiBold,
    fontSize: 18,
    fontWeight: "500" as const,
    lineHeight: 24,
    letterSpacing: 0.1,
  },

  // Body text - For readable blocks of text
  bodyLarge: {
    fontFamily: fontFamily.regular,
    fontSize: 16,
    fontWeight: "400" as const,
    lineHeight: 24,
    letterSpacing: 0.5,
  },
  bodyMedium: {
    fontFamily: fontFamily.regular,
    fontSize: 14,
    fontWeight: "400" as const,
    lineHeight: 20,
    letterSpacing: 0.25,
  },
  bodySmall: {
    fontFamily: fontFamily.regular,
    fontSize: 12,
    fontWeight: "400" as const,
    lineHeight: 16,
    letterSpacing: 0.4,
  },

  // Labels - For UI elements, buttons, and form controls
  labelLarge: {
    fontFamily: fontFamily.medium,
    fontSize: 14,
    fontWeight: "500" as const,
    lineHeight: 20,
    letterSpacing: 0.1,
  },
  labelMedium: {
    fontFamily: fontFamily.medium,
    fontSize: 12,
    fontWeight: "500" as const,
    lineHeight: 16,
    letterSpacing: 0.5,
  },
  labelSmall: {
    fontFamily: fontFamily.medium,
    fontSize: 11,
    fontWeight: "500" as const,
    lineHeight: 16,
    letterSpacing: 0.5,
  },

  // Legacy aliases for backward compatibility
  title: {
    fontFamily: fontFamily.bold,
    fontSize: 22,
    fontWeight: "600" as const,
    lineHeight: 28,
  },
  subtitle: {
    fontFamily: fontFamily.semiBold,
    fontSize: 16,
    fontWeight: "600" as const,
    lineHeight: 24,
  },
  body: {
    fontFamily: fontFamily.regular,
    fontSize: 14,
    fontWeight: "400" as const,
    lineHeight: 20,
  },
  caption: {
    fontFamily: fontFamily.regular,
    fontSize: 12,
    fontWeight: "400" as const,
    lineHeight: 16,
  },
  overline: {
    fontFamily: fontFamily.medium,
    fontSize: 10,
    fontWeight: "500" as const,
    lineHeight: 16,
    textTransform: "uppercase" as const,
    letterSpacing: 1.5,
  },
  button: {
    fontFamily: fontFamily.semiBold,
    fontSize: 14,
    fontWeight: "600" as const,
    lineHeight: 20,
    letterSpacing: 0.25,
  },

  // Extended variants for cybersecurity app
  newsTitle: {
    fontFamily: fontFamily.bold,
    fontSize: 18,
    fontWeight: "600" as const,
    lineHeight: 24,
    letterSpacing: -0.1,
  },
  newsSource: {
    fontFamily: fontFamily.medium,
    fontSize: 12,
    fontWeight: "500" as const,
    lineHeight: 16,
    letterSpacing: 0.4,
  },
  newsTimestamp: {
    fontFamily: fontFamily.regular,
    fontSize: 11,
    fontWeight: "400" as const,
    lineHeight: 16,
    letterSpacing: 0.5,
  },
  cardTitle: {
    fontFamily: fontFamily.semiBold,
    fontSize: 16,
    fontWeight: "600" as const,
    lineHeight: 22,
    letterSpacing: -0.05,
  },
  cardSubtitle: {
    fontFamily: fontFamily.regular,
    fontSize: 14,
    fontWeight: "400" as const,
    lineHeight: 20,
    letterSpacing: 0.1,
  },
  badge: {
    fontFamily: fontFamily.medium,
    fontSize: 10,
    fontWeight: "500" as const,
    lineHeight: 14,
    letterSpacing: 0.8,
    textTransform: "uppercase" as const,
  },
  
  // Interactive text styles
  link: {
    fontFamily: fontFamily.medium,
    fontSize: 14,
    fontWeight: "500" as const,
    lineHeight: 20,
    letterSpacing: 0.1,
    textDecorationLine: "underline" as const,
  },
  
  // Cybersecurity specific
  threatLevel: {
    fontFamily: fontFamily.bold,
    fontSize: 12,
    fontWeight: "700" as const,
    lineHeight: 16,
    letterSpacing: 1,
    textTransform: "uppercase" as const,
  },
  securityBadge: {
    fontFamily: fontFamily.bold,
    fontSize: 10,
    fontWeight: "600" as const,
    lineHeight: 14,
    letterSpacing: 0.5,
    textTransform: "uppercase" as const,
  },
  riskScore: {
    fontFamily: fontFamily.semiBold,
    fontSize: 11,
    fontWeight: "600" as const,
    lineHeight: 14,
    letterSpacing: 0.25,
  },
}