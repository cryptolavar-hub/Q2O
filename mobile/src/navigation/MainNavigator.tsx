/**
 * Main Navigation for Quick2Odoo Mobile Dashboard
 */

import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

// Screens
import DashboardScreen from '../screens/DashboardScreen';
import NewProjectScreen from '../screens/NewProjectScreen';
import MetricsScreen from '../screens/MetricsScreen';
import SettingsScreen from '../screens/SettingsScreen';
import ProjectDetailsScreen from '../screens/ProjectDetailsScreen';

const Tab = createBottomTabNavigator();
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

const MainNavigator = () => {
  return (
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
      <Tab.Screen name="Dashboard" component={DashboardStack} />
      <Tab.Screen name="New Project" component={NewProjectScreen} />
      <Tab.Screen name="Metrics" component={MetricsScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
};

export default MainNavigator;

