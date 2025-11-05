/**
 * Quick2Odoo Mobile Dashboard
 * Multi-Platform to Odoo v18 Migration - Real-time Monitoring & Control
 * 
 * Features:
 * - Real-time WebSocket dashboard
 * - Project initiation and monitoring
 * - Multi-platform support visualization
 * - Agent activity tracking
 * - Metrics and analytics
 * - Dark mode support
 * - Tablet-optimized layouts
 */

import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { Provider as PaperProvider } from 'react-native-paper';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar, useColorScheme } from 'react-native';
import MainNavigator from './src/navigation/MainNavigator';
import { DashboardProvider } from './src/services/DashboardContext';
import ThemeManager from './src/utils/ThemeManager';
import { getTheme } from './src/utils/theme';

const App = () => {
  const systemColorScheme = useColorScheme();
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    // Initialize theme manager
    ThemeManager.initialize().then(() => {
      setIsDark(ThemeManager.isDarkMode());
    });

    // Listen to theme changes
    const unsubscribe = ThemeManager.onThemeChange((mode, dark) => {
      setIsDark(dark);
    });

    // Listen to system theme changes
    const systemSub = ThemeManager.subscribeToSystemChanges();

    return () => {
      unsubscribe();
      systemSub?.remove();
    };
  }, []);

  const theme = getTheme(isDark);

  return (
    <SafeAreaProvider>
      <PaperProvider theme={theme}>
        <DashboardProvider>
          <NavigationContainer theme={theme}>
            <StatusBar
              barStyle={isDark ? 'light-content' : 'dark-content'}
              backgroundColor={theme.colors.surface}
            />
            <MainNavigator />
          </NavigationContainer>
        </DashboardProvider>
      </PaperProvider>
    </SafeAreaProvider>
  );
};

export default App;

