import React from 'react';
import {createStackNavigator} from '@react-navigation/stack';
import {'filename': 'login', 'class_name': 'Login', 'variable_name': 'login', 'function_name': 'login', 'display_name': 'Login', 'original': 'Login'}Screen from '../screens/loginScreen';
import {'filename': 'register', 'class_name': 'Register', 'variable_name': 'register', 'function_name': 'register', 'display_name': 'Register', 'original': 'Register'}Screen from '../screens/registerScreen';
import {'filename': 'forgotpassword', 'class_name': 'Forgotpassword', 'variable_name': 'forgotpassword', 'function_name': 'forgotpassword', 'display_name': 'ForgotPassword', 'original': 'ForgotPassword'}Screen from '../screens/forgotpasswordScreen';
import {'filename': 'home', 'class_name': 'Home', 'variable_name': 'home', 'function_name': 'home', 'display_name': 'Home', 'original': 'Home'}Screen from '../screens/homeScreen';
import {'filename': 'profile', 'class_name': 'Profile', 'variable_name': 'profile', 'function_name': 'profile', 'display_name': 'Profile', 'original': 'Profile'}Screen from '../screens/profileScreen';
import {'filename': 'settings', 'class_name': 'Settings', 'variable_name': 'settings', 'function_name': 'settings', 'display_name': 'Settings', 'original': 'Settings'}Screen from '../screens/settingsScreen';
import {'filename': 'notifications', 'class_name': 'Notifications', 'variable_name': 'notifications', 'function_name': 'notifications', 'display_name': 'Notifications', 'original': 'Notifications'}Screen from '../screens/notificationsScreen';

const Stack = createStackNavigator();

export default function RootNavigator() {
  return (
    <Stack.Navigator>
      <Stack.Screen name="{'filename': 'login', 'class_name': 'Login', 'variable_name': 'login', 'function_name': 'login', 'display_name': 'Login', 'original': 'Login'}" component={{'filename': 'login', 'class_name': 'Login', 'variable_name': 'login', 'function_name': 'login', 'display_name': 'Login', 'original': 'Login'}Screen} />
      <Stack.Screen name="{'filename': 'register', 'class_name': 'Register', 'variable_name': 'register', 'function_name': 'register', 'display_name': 'Register', 'original': 'Register'}" component={{'filename': 'register', 'class_name': 'Register', 'variable_name': 'register', 'function_name': 'register', 'display_name': 'Register', 'original': 'Register'}Screen} />
      <Stack.Screen name="{'filename': 'forgotpassword', 'class_name': 'Forgotpassword', 'variable_name': 'forgotpassword', 'function_name': 'forgotpassword', 'display_name': 'ForgotPassword', 'original': 'ForgotPassword'}" component={{'filename': 'forgotpassword', 'class_name': 'Forgotpassword', 'variable_name': 'forgotpassword', 'function_name': 'forgotpassword', 'display_name': 'ForgotPassword', 'original': 'ForgotPassword'}Screen} />
      <Stack.Screen name="{'filename': 'home', 'class_name': 'Home', 'variable_name': 'home', 'function_name': 'home', 'display_name': 'Home', 'original': 'Home'}" component={{'filename': 'home', 'class_name': 'Home', 'variable_name': 'home', 'function_name': 'home', 'display_name': 'Home', 'original': 'Home'}Screen} />
      <Stack.Screen name="{'filename': 'profile', 'class_name': 'Profile', 'variable_name': 'profile', 'function_name': 'profile', 'display_name': 'Profile', 'original': 'Profile'}" component={{'filename': 'profile', 'class_name': 'Profile', 'variable_name': 'profile', 'function_name': 'profile', 'display_name': 'Profile', 'original': 'Profile'}Screen} />
      <Stack.Screen name="{'filename': 'settings', 'class_name': 'Settings', 'variable_name': 'settings', 'function_name': 'settings', 'display_name': 'Settings', 'original': 'Settings'}" component={{'filename': 'settings', 'class_name': 'Settings', 'variable_name': 'settings', 'function_name': 'settings', 'display_name': 'Settings', 'original': 'Settings'}Screen} />
      <Stack.Screen name="{'filename': 'notifications', 'class_name': 'Notifications', 'variable_name': 'notifications', 'function_name': 'notifications', 'display_name': 'Notifications', 'original': 'Notifications'}" component={{'filename': 'notifications', 'class_name': 'Notifications', 'variable_name': 'notifications', 'function_name': 'notifications', 'display_name': 'Notifications', 'original': 'Notifications'}Screen} />
    </Stack.Navigator>
  );
}
