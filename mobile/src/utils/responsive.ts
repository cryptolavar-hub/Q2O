/**
 * Responsive Utilities for Tablet Optimization
 * Provides breakpoints and responsive layout helpers
 */

import { Dimensions, Platform } from 'react-native';

const { width, height } = Dimensions.get('window');

// Breakpoints
export const BREAKPOINTS = {
  phone: 0,
  tablet: 768,
  desktop: 1024,
};

// Device type detection
export const isTablet = () => {
  const aspectRatio = height / width;
  return (
    width >= BREAKPOINTS.tablet &&
    (Platform.OS === 'ios' ? aspectRatio < 1.6 : aspectRatio < 1.6)
  );
};

export const isPhone = () => !isTablet();

// Responsive values
export const getResponsiveValue = <T,>(phoneValue: T, tabletValue: T): T => {
  return isTablet() ? tabletValue : phoneValue;
};

// Spacing
export const spacing = {
  xs: getResponsiveValue(4, 6),
  sm: getResponsiveValue(8, 12),
  md: getResponsiveValue(16, 24),
  lg: getResponsiveValue(24, 32),
  xl: getResponsiveValue(32, 48),
};

// Typography
export const fontSize = {
  xs: getResponsiveValue(10, 12),
  sm: getResponsiveValue(12, 14),
  md: getResponsiveValue(14, 16),
  lg: getResponsiveValue(16, 18),
  xl: getResponsiveValue(20, 24),
  xxl: getResponsiveValue(24, 32),
};

// Grid columns
export const getGridColumns = () => {
  return isTablet() ? 2 : 1;
};

// Card width for grid layouts
export const getCardWidth = (marginHorizontal: number = 16) => {
  const columns = getGridColumns();
  const totalMargin = marginHorizontal * 2; // Left and right margins
  const gap = columns > 1 ? 16 : 0; // Gap between columns
  
  return (width - totalMargin - gap) / columns;
};

// Orientation detection
export const isLandscape = () => width > height;
export const isPortrait = () => height > width;

// Safe area helpers
export const getScreenDimensions = () => ({
  width,
  height,
  isTablet: isTablet(),
  isPhone: isPhone(),
  isLandscape: isLandscape(),
  isPortrait: isPortrait(),
});

// Responsive font size based on screen width
export const responsiveFontSize = (baseSize: number) => {
  const scale = width / 375; // Base width (iPhone X)
  const newSize = baseSize * scale;
  return Math.round(newSize);
};

// Responsive spacing
export const responsiveSpacing = (baseSpacing: number) => {
  return isTablet() ? baseSpacing * 1.5 : baseSpacing;
};

