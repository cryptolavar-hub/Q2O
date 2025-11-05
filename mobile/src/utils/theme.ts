/**
 * Theme Configuration for Dark Mode Support
 * Provides light and dark themes using React Native Paper
 */

import { MD3LightTheme, MD3DarkTheme } from 'react-native-paper';

export const lightTheme = {
  ...MD3LightTheme,
  colors: {
    ...MD3LightTheme.colors,
    primary: '#2196F3',
    secondary: '#03A9F4',
    tertiary: '#00BCD4',
    error: '#f44336',
    background: '#f5f5f5',
    surface: '#ffffff',
    surfaceVariant: '#e3f2fd',
    onSurface: '#000000',
    onSurfaceVariant: '#666666',
    outline: '#cccccc',
    success: '#4caf50',
    warning: '#ff9800',
    info: '#2196F3',
  },
};

export const darkTheme = {
  ...MD3DarkTheme,
  colors: {
    ...MD3DarkTheme.colors,
    primary: '#90CAF9',
    secondary: '#81D4FA',
    tertiary: '#80DEEA',
    error: '#ef5350',
    background: '#121212',
    surface: '#1E1E1E',
    surfaceVariant: '#263238',
    onSurface: '#ffffff',
    onSurfaceVariant: '#b0bec5',
    outline: '#37474f',
    success: '#66bb6a',
    warning: '#ffa726',
    info: '#42a5f5',
  },
};

export type ThemeMode = 'light' | 'dark' | 'system';

export const getTheme = (isDark: boolean) => {
  return isDark ? darkTheme : lightTheme;
};
