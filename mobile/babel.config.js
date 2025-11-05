module.exports = {
  presets: ['module:metro-react-native-babel-preset'],
  plugins: [
    'react-native-reanimated/plugin',
    [
      'module-resolver',
      {
        root: ['./src'],
        extensions: ['.ios.ts', '.android.ts', '.ts', '.ios.tsx', '.android.tsx', '.tsx', '.jsx', '.js', '.json'],
        alias: {
          '@components': './src/components',
          '@screens': './src/screens',
          '@services': './src/services',
          '@navigation': './src/navigation',
          '@utils': './src/utils',
        }
      }
    ]
  ]
};

