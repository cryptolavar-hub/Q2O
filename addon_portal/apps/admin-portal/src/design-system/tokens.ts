export const colors = {
  brand: {
    pink: '#FF6B9D',
    rose: '#C44569',
    purple: '#9B59B6',
    violet: '#8E44AD',
    indigo: '#6C3483',
  },
  neutrals: {
    white: '#FFFFFF',
    gray50: '#F9FAFB',
    gray100: '#F3F4F6',
    gray200: '#E5E7EB',
    gray300: '#D1D5DB',
    gray500: '#6B7280',
    gray700: '#374151',
    gray900: '#111827',
  },
  status: {
    success: '#22C55E',
    warning: '#FACC15',
    error: '#EF4444',
    info: '#3B82F6',
  },
};

export const gradients = {
  brand:
    'linear-gradient(135deg, #FF6B9D 0%, #C44569 25%, #9B59B6 50%, #8E44AD 75%, #6C3483 100%)',
  success: 'linear-gradient(135deg, #22C55E 0%, #16A34A 100%)',
  warning: 'linear-gradient(135deg, #FACC15 0%, #F97316 100%)',
  error: 'linear-gradient(135deg, #EF4444 0%, #B91C1C 100%)',
  subtle: 'linear-gradient(135deg, rgba(255,107,157,0.1) 0%, rgba(108,52,131,0.1) 100%)',
};

export const spacing = {
  none: '0px',
  xs: '4px',
  sm: '8px',
  md: '12px',
  lg: '16px',
  xl: '24px',
  '2xl': '32px',
  '3xl': '48px',
};

export const radii = {
  sm: '6px',
  md: '12px',
  lg: '16px',
  xl: '24px',
  full: '9999px',
};

export const shadows = {
  xs: '0 1px 2px 0 rgba(15, 23, 42, 0.05)',
  sm: '0 2px 6px -1px rgba(15, 23, 42, 0.08)',
  md: '0 8px 20px rgba(15, 23, 42, 0.12)',
  lg: '0 20px 45px rgba(15, 23, 42, 0.14)',
};

export const typography = {
  fontFamily: "'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  heading: {
    xl: { fontSize: '2.25rem', lineHeight: '2.75rem', fontWeight: 700 },
    lg: { fontSize: '1.875rem', lineHeight: '2.25rem', fontWeight: 700 },
    md: { fontSize: '1.5rem', lineHeight: '1.875rem', fontWeight: 700 },
    sm: { fontSize: '1.25rem', lineHeight: '1.625rem', fontWeight: 600 },
  },
  body: {
    md: { fontSize: '1rem', lineHeight: '1.5rem', fontWeight: 500 },
    sm: { fontSize: '0.875rem', lineHeight: '1.25rem', fontWeight: 500 },
  },
  caption: { fontSize: '0.75rem', lineHeight: '1rem', fontWeight: 500 },
};

export const transitions = {
  base: 'all 200ms ease',
  bounce: 'transform 200ms cubic-bezier(0.34, 1.56, 0.64, 1)',
};

export const blur = {
  sm: '4px',
  md: '12px',
  glass: '20px',
};

export type ColorToken = typeof colors;
