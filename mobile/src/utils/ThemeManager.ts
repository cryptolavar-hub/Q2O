/**
 * Theme Manager - Centralized Theme Control
 * Manages dark mode, system theme, and theme persistence
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import { Appearance, AppearanceChangeListener } from 'react-native';

export type ThemeMode = 'light' | 'dark' | 'system';

type ThemeChangeCallback = (mode: ThemeMode, isDark: boolean) => void;

class ThemeManagerClass {
  private currentMode: ThemeMode = 'system';
  private listeners: Set<ThemeChangeCallback> = new Set();
  private systemListener: AppearanceChangeListener | null = null;
  private readonly STORAGE_KEY = 'app_theme_mode';

  async initialize() {
    try {
      const saved = await AsyncStorage.getItem(this.STORAGE_KEY);
      if (saved && (saved === 'light' || saved === 'dark' || saved === 'system')) {
        this.currentMode = saved as ThemeMode;
      }
    } catch (error) {
      console.error('[ThemeManager] Failed to load theme:', error);
    }
  }

  async setThemeMode(mode: ThemeMode) {
    try {
      this.currentMode = mode;
      await AsyncStorage.setItem(this.STORAGE_KEY, mode);
      this.notifyListeners();
    } catch (error) {
      console.error('[ThemeManager] Failed to save theme:', error);
    }
  }

  getThemeMode(): ThemeMode {
    return this.currentMode;
  }

  isDarkMode(): boolean {
    if (this.currentMode === 'system') {
      return Appearance.getColorScheme() === 'dark';
    }
    return this.currentMode === 'dark';
  }

  async toggleTheme() {
    const modes: ThemeMode[] = ['light', 'dark', 'system'];
    const currentIndex = modes.indexOf(this.currentMode);
    const nextMode = modes[(currentIndex + 1) % modes.length];
    await this.setThemeMode(nextMode);
  }

  onThemeChange(callback: ThemeChangeCallback): () => void {
    this.listeners.add(callback);
    return () => {
      this.listeners.delete(callback);
    };
  }

  subscribeToSystemChanges() {
    if (this.currentMode === 'system') {
      this.systemListener = Appearance.addChangeListener(() => {
        this.notifyListeners();
      });
      return this.systemListener;
    }
    return null;
  }

  private notifyListeners() {
    const isDark = this.isDarkMode();
    this.listeners.forEach(callback => {
      callback(this.currentMode, isDark);
    });
  }
}

const ThemeManager = new ThemeManagerClass();
export default ThemeManager;
