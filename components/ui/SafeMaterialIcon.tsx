import { MaterialIcons } from '@expo/vector-icons';
import { Feather } from '@expo/vector-icons';

interface SafeMaterialIconProps {
  name: string;
  size: number;
  color: string;
  fallbackIcon?: keyof typeof Feather.glyphMap;
}

// Map of common invalid MaterialIcon names to valid ones
const iconMap: Record<string, string> = {
  'light-mode': 'wb-sunny',
  'dark-mode': 'nights-stay',
  'search-off': 'search',
  'cloud-done': 'cloud-queue',
  'auto-awesome': 'star',
  'lightbulb': 'lightbulb-outline',
  'done-all': 'done',
  'clear-all': 'clear',
  'open-in-new': 'open-in-browser',
};

// Valid MaterialIcon names that we know exist
const validIcons = new Set([
  'home', 'search', 'notifications', 'bookmark', 'arrow-back', 'close', 
  'article', 'security', 'schedule', 'person', 'share', 'wb-sunny', 
  'nights-stay', 'cloud-queue', 'star', 'lightbulb-outline', 'done', 
  'clear', 'open-in-browser'
]);

export function SafeMaterialIcon({ name, size, color, fallbackIcon = 'help-circle' }: SafeMaterialIconProps) {
  // Map the icon name if it's in our mapping
  const mappedName = iconMap[name] || name;
  
  try {
    // Check if the icon exists in MaterialIcons
    if (validIcons.has(mappedName) || (MaterialIcons as any).glyphMap[mappedName]) {
      return (
        <MaterialIcons 
          name={mappedName as any} 
          size={size} 
          color={color} 
        />
      );
    } else {
      // Fallback to Feather icon
      return (
        <Feather 
          name={fallbackIcon} 
          size={size} 
          color={color} 
        />
      );
    }
  } catch (error) {
    // Ultimate fallback to Feather icon
    return (
      <Feather 
        name={fallbackIcon} 
        size={size} 
        color={color} 
      />
    );
  }
}
