import { Dimensions, Platform } from 'react-native';

const { width, height } = Dimensions.get('window');

// Material Design 3 Layout Constants
export const Layout = {
  // Screen dimensions
  window: {
    width,
    height,
  },
  
  // Breakpoints for responsive design
  breakpoints: {
    compact: 600,      // Phones in portrait
    medium: 840,       // Tablets in portrait, phones in landscape  
    expanded: 1200,    // Tablets in landscape, desktops
  },
  
  // Spacing system based on 4px grid
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
    xxxl: 64,
  },
  
  // Border radius system
  borderRadius: {
    none: 0,
    xs: 4,
    sm: 8,
    md: 12,
    lg: 16,
    xl: 20,
    xxl: 28,
    full: 9999,
  },
  
  // Material Design 3 elevation levels
  elevation: {
    none: 0,
    xs: 1,
    sm: 2,
    md: 3,
    lg: 4,
    xl: 5,
  },
  
  // Component sizes
  components: {
    header: {
      height: Platform.OS === 'ios' ? 88 : 64,
      heightLarge: 120,
    },
    tabBar: {
      height: Platform.OS === 'ios' ? 83 : 64,
    },
    button: {
      height: 48,
      heightSmall: 36,
      heightLarge: 56,
    },
    searchBar: {
      height: 48,
    },
    card: {
      minHeight: 120,
      imageHeight: 200,
      compactHeight: 80,
    },
    avatar: {
      small: 32,
      medium: 48,
      large: 64,
    },
    icon: {
      small: 16,
      medium: 24,
      large: 32,
    },
  },
  
  // Animation timing
  animation: {
    fast: 150,
    normal: 250,
    slow: 350,
  },
  
  // Z-index layers
  zIndex: {
    background: -1,
    base: 0,
    docked: 10,
    dropdown: 1000,
    sticky: 1100,
    banner: 1200,
    overlay: 1300,
    modal: 1400,
    popover: 1500,
    skipLink: 1600,
    toast: 1700,
    tooltip: 1800,
  },
  
  // Safe area constants
  safeArea: {
    paddingTop: Platform.OS === 'ios' ? 44 : 24,
    paddingBottom: Platform.OS === 'ios' ? 34 : 0,
  },
  
  // Responsive helpers
  isSmallDevice: width < 375,
  isLargeDevice: width > 414,
  isTablet: width >= 768,
  
  // Screen type based on width
  getScreenType: () => {
    if (width < 600) return 'compact';
    if (width < 840) return 'medium';
    return 'expanded';
  },
  
  // Grid system
  grid: {
    columns: 12,
    gutter: 16,
    margin: 16,
  },
  
  // News app specific layouts
  news: {
    cardSpacing: 16,
    sectionSpacing: 24,
    listPadding: 16,
    headerHeight: 160,
    categoryHeight: 120,
  },
};
