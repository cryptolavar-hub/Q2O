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
 */

import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { Provider as PaperProvider } from 'react-native-paper';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { StatusBar } from 'react-native';
import MainNavigator from './src/navigation/MainNavigator';
import { DashboardProvider } from './src/services/DashboardContext';

const App = () => {
  return (
    <SafeAreaProvider>
      <PaperProvider>
        <DashboardProvider>
          <NavigationContainer>
            <StatusBar barStyle="dark-content" backgroundColor="#ffffff" />
            <MainNavigator />
          </NavigationContainer>
        </DashboardProvider>
      </PaperProvider>
    </SafeAreaProvider>
  );
};

export default App;

