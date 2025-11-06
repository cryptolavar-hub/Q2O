/**
 * Main Navigation for Quick2Odoo Mobile Dashboard
 * Supports both phone (bottom tabs) and tablet (drawer) layouts
 */

import React, { useState, useEffect } from 'react';
import { Dimensions } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createDrawerNavigator } from '@react-navigation/drawer';
import { createStackNavigator } from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import ResponsiveLayout from '../utils/ResponsiveLayout';

// Screens
import DashboardScreen from '../screens/DashboardScreen';
import NewProjectScreen from '../screens/NewProjectScreen';
import MetricsScreen from '../screens/MetricsScreen';
import SettingsScreen from '../screens/SettingsScreen';
import ProjectDetailsScreen from '../screens/ProjectDetailsScreen';

const Tab = createBottomTabNavigator();
const Drawer = createDrawerNavigator();
const Stack = createStackNavigator();

const DashboardStack = () => (
  <Stack.Navigator>
    <Stack.Screen 
      name="DashboardHome" 
      component={DashboardScreen}
      options={{ title: 'Quick2Odoo Dashboard' }}
    />
    <Stack.Screen 
      name="ProjectDetails" 
      component={ProjectDetailsScreen}
      options={{ title: 'Project Details' }}
    />
  </Stack.Navigator>
);

// Drawer Navigator for Tablets
const DrawerNavigator = () => (
  <Drawer.Navigator
    screenOptions={{
      drawerActiveTintColor: '#2196F3',
      drawerInactiveTintColor: 'gray',
    }}
  >
    {/* PHASE 1: Building Solutions (Agents work here) */}
    <Drawer.Screen 
      name="Dashboard" 
      component={DashboardStack}
      options={{
        drawerIcon: ({ color, size }) => <Icon name="view-dashboard" size={size} color={color} />,
        drawerLabel: '📊 Dashboard (Monitor Agents)',
      }}
    />
    <Drawer.Screen 
      name="New Project" 
      component={NewProjectScreen}
      options={{
        drawerIcon: ({ color, size }) => <Icon name="plus-circle" size={size} color={color} />,
        drawerLabel: '🏗️ New Project (Have Agents Build)',
      }}
    />
    
    {/* Monitoring & Analytics */}
    <Drawer.Screen 
      name="Metrics" 
      component={MetricsScreen}
      options={{
        drawerIcon: ({ color, size }) => <Icon name="chart-line" size={size} color={color} />,
        drawerLabel: '📈 Metrics',
      }}
    />
    
    {/* Configuration */}
    <Drawer.Screen 
      name="Settings" 
      component={SettingsScreen}
      options={{
        drawerIcon: ({ color, size }) => <Icon name="cog" size={size} color={color} />,
        drawerLabel: '⚙️ Settings',
      }}
    />
    
    {/* Note: Billing screens (Phase 2) are accessed via navigation.navigate() */}
  </Drawer.Navigator>
);

// Tab Navigator for Phones
const TabNavigator = () => (
  <Tab.Navigator
    screenOptions={({ route }) => ({
      tabBarIcon: ({ focused, color, size }) => {
        let iconName = 'home';

        if (route.name === 'Dashboard') {
          iconName = focused ? 'view-dashboard' : 'view-dashboard-outline';
        } else if (route.name === 'New Project') {
          iconName = focused ? 'plus-circle' : 'plus-circle-outline';
        } else if (route.name === 'Metrics') {
          iconName = focused ? 'chart-line' : 'chart-line-variant';
        } else if (route.name === 'Settings') {
          iconName = focused ? 'cog' : 'cog-outline';
        }

        return <Icon name={iconName} size={size} color={color} />;
      },
      tabBarActiveTintColor: '#2196F3',
      tabBarInactiveTintColor: 'gray',
      headerShown: false,
    })}
  >
    {/* PHASE 1: Building Solutions (Agents Build) */}
    <Tab.Screen 
      name="Dashboard" 
      component={DashboardStack}
      options={{ title: 'Monitor Agents' }}
    />
    <Tab.Screen 
      name="New Project" 
      component={NewProjectScreen}
      options={{ title: 'Have Agents Build' }}
    />
    
    {/* Monitoring & Configuration */}
    <Tab.Screen 
      name="Metrics" 
      component={MetricsScreen}
      options={{ title: 'Metrics' }}
    />
    <Tab.Screen 
      name="Settings" 
      component={SettingsScreen}
      options={{ title: 'Settings' }}
    />
    
    {/* Note: Billing screens (Phase 2) accessed via navigation.navigate() from other screens */}
  </Tab.Navigator>
);

const MainNavigator = () => {
  const [isTablet, setIsTablet] = useState(false);

  useEffect(() => {
    const updateLayout = () => {
      const deviceInfo = ResponsiveLayout.getDeviceInfo();
      setIsTablet(deviceInfo.isTablet);
    };

    updateLayout();

    const subscription = Dimensions.addEventListener('change', updateLayout);
    return () => subscription?.remove();
  }, []);

  // Use drawer navigation for tablets, bottom tabs for phones
  return isTablet ? <DrawerNavigator /> : <TabNavigator />;
};

export default MainNavigator;

