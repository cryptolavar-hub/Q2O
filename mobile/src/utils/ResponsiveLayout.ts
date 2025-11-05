/**
 * Responsive Layout Utilities - Tablet Optimization
 * Provides responsive breakpoints and layout helpers
 */

import { Dimensions, Platform } from 'react-native';

export interface DeviceInfo {
  isPhone: boolean;
  isTablet: boolean;
  isSmallTablet: boolean;
  isLargeTablet: boolean;
  screenWidth: number;
  screenHeight: number;
  orientation: 'portrait' | 'landscape';
}

class ResponsiveLayout {
  private PHONE_MAX_WIDTH = 600;
  private SMALL_TABLET_MAX_WIDTH = 900;
  private LARGE_TABLET_MIN_WIDTH = 900;

  getDeviceInfo(): DeviceInfo {
    const { width, height } = Dimensions.get('window');
    const isTablet = width >= this.PHONE_MAX_WIDTH;
    const isSmallTablet = width >= this.PHONE_MAX_WIDTH && width < this.SMALL_TABLET_MAX_WIDTH;
    const isLargeTablet = width >= this.LARGE_TABLET_MIN_WIDTH;
    const orientation = width > height ? 'landscape' : 'portrait';

    return {
      isPhone: !isTablet,
      isTablet,
      isSmallTablet,
      isLargeTablet,
      screenWidth: width,
      screenHeight: height,
      orientation,
    };
  }

  getColumns(): number {
    const info = this.getDeviceInfo();
    if (info.isLargeTablet && info.orientation === 'landscape') {
      return 3;
    } else if (info.isTablet) {
      return 2;
    }
    return 1;
  }

  getCardWidth(): string {
    const columns = this.getColumns();
    if (columns === 1) return '100%';
    if (columns === 2) return '48%';
    return '31%';
  }

  shouldUseDrawer(): boolean {
    const info = this.getDeviceInfo();
    return info.isTablet;
  }

  getFontScale(): number {
    const info = this.getDeviceInfo();
    if (info.isLargeTablet) return 1.2;
    if (info.isTablet) return 1.1;
    return 1.0;
  }

  getSpacing(base: number = 8): number {
    const info = this.getDeviceInfo();
    if (info.isLargeTablet) return base * 1.5;
    if (info.isTablet) return base * 1.25;
    return base;
  }
}

export default new ResponsiveLayout();

