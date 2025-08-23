const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Add support for SVG
config.transformer.assetPlugins = ['expo-asset/tools/hashAssetFiles'];

// Add resolver configuration for better module resolution
config.resolver.platforms = ['native', 'android', 'ios', 'web'];

// Optimize for production builds
config.transformer.minifierConfig = {
  keep_fnames: true,
  mangle: {
    keep_fnames: true,
  },
};

module.exports = config;
