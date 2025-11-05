# Quick2Odoo Mobile Dashboard

**Real-time Monitoring & Control for Multi-Platform to Odoo v18 Migration**

A comprehensive React Native mobile application for Android and iOS that provides full dashboard functionality and project initiation capabilities for the Quick2Odoo multi-agent system.

---

## 📱 Features

### ✨ **Complete Dashboard Functionality**
- ✅ Real-time WebSocket connection to backend
- ✅ Live project monitoring and task tracking
- ✅ Agent activity feed
- ✅ System metrics and analytics
- ✅ Multi-platform visualization
- ✅ Task progress tracking with statistics

### 🚀 **Project Initiation**
- ✅ Start new projects from mobile
- ✅ Multi-platform selection (QuickBooks, SAGE, Wave, Expensify, doola, Dext, etc.)
- ✅ Define objectives and requirements
- ✅ Real-time project status updates
- ✅ Example project templates

### 📊 **Real-Time Monitoring**
- ✅ Live task updates via WebSocket
- ✅ Agent activity tracking
- ✅ Project completion status
- ✅ System health monitoring
- ✅ Metrics dashboard

### 🎨 **Professional UI/UX**
- ✅ Material Design components
- ✅ Responsive layout for tablets
- ✅ Pull-to-refresh functionality
- ✅ Offline mode indicators
- ✅ Loading states and error handling

---

## 🏗️ Architecture

### **Tech Stack**
- **Framework**: React Native 0.72.6
- **Navigation**: React Navigation 6.x
- **UI Components**: React Native Paper
- **WebSocket**: Socket.IO Client
- **HTTP Client**: Axios
- **State Management**: React Context API
- **Charts**: React Native Chart Kit
- **Icons**: React Native Vector Icons

### **Project Structure**
```
mobile/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ConnectionStatus.tsx
│   │   ├── TaskCard.tsx
│   │   └── AgentActivityFeed.tsx
│   ├── screens/            # Main application screens
│   │   ├── DashboardScreen.tsx
│   │   ├── NewProjectScreen.tsx
│   │   ├── MetricsScreen.tsx
│   │   ├── SettingsScreen.tsx
│   │   └── ProjectDetailsScreen.tsx
│   ├── services/           # Backend communication
│   │   ├── DashboardWebSocket.ts
│   │   ├── ApiService.ts
│   │   └── DashboardContext.tsx
│   ├── navigation/         # Navigation configuration
│   │   └── MainNavigator.tsx
│   └── utils/              # Utility functions
├── android/                # Android-specific code
├── ios/                    # iOS-specific code
├── App.tsx                 # Main application component
├── index.js                # Entry point
└── package.json            # Dependencies
```

---

## 🚀 Getting Started

### **Prerequisites**
- Node.js 18.x or higher
- npm 9.x or higher
- React Native CLI
- Android Studio (for Android)
- Xcode (for iOS, macOS only)

### **Installation**

1. **Navigate to mobile directory**
```bash
cd mobile
```

2. **Install dependencies**
```bash
npm install
```

3. **Install iOS dependencies (macOS only)**
```bash
cd ios && pod install && cd ..
```

4. **Start Metro bundler**
```bash
npm start
```

5. **Run on Android**
```bash
npm run android
```

6. **Run on iOS (macOS only)**
```bash
npm run ios
```

---

## 📋 Configuration

### **Backend Server Setup**

1. Open the app and navigate to **Settings**
2. Enter your Quick2Odoo backend server URL:
   - Local development: `http://10.0.2.2:8000` (Android emulator)
   - Local development: `http://localhost:8000` (iOS simulator)
   - Production: `https://your-server.com`
3. Tap **Connect**
4. Verify connection status on Dashboard

### **Environment Variables**

Create `.env` file in mobile directory (optional):
```env
API_BASE_URL=http://localhost:8000
WS_BASE_URL=http://localhost:8000
```

---

## 📱 Screens Overview

### **1. Dashboard Screen**
- Real-time project monitoring
- Current project details with platforms
- Task statistics and progress
- Recent task list
- Agent activity feed
- Connection status indicator

### **2. New Project Screen**
- Project description input
- Multi-platform selection (QuickBooks, SAGE, Wave, etc.)
- Dynamic objectives list
- Form validation
- Example project loader
- Submit to orchestrator

### **3. Metrics Screen**
- System resource usage (CPU, Memory)
- Agent statistics
- Task completion rates
- Success/failure metrics
- Historical charts

### **4. Settings Screen**
- Server URL configuration
- Connection management
- App version information
- About section
- Disconnect option

### **5. Project Details Screen**
- Complete project information
- Full objectives list
- All task details
- Timeline view
- Export capabilities

---

## 🔌 API Integration

### **WebSocket Events (Real-time)**
```typescript
// Listening to events
- 'project_start': New project initiated
- 'task_update': Task status changed
- 'task_complete': Task finished
- 'agent_activity': Agent performed action
- 'metric_update': System metrics updated
- 'project_complete': Project finished
```

### **REST API Endpoints**
```typescript
POST /api/projects/start
GET  /api/projects/:id/status
GET  /api/metrics
GET  /api/agents/status
GET  /health
```

---

## 🎨 Component Library

### **Reusable Components**

**ConnectionStatus**
- Displays WebSocket connection state
- Visual indicator (connected/disconnected)
- Automatic reconnection status

**TaskCard**
- Individual task display
- Progress indicator
- Status badge
- Agent type icon

**AgentActivityFeed**
- Scrollable activity list
- Timestamp formatting
- Activity type indicators
- Real-time updates

---

## 🧪 Testing

### **Run Tests**
```bash
npm test
```

### **Test Coverage**
```bash
npm run test:coverage
```

### **Linting**
```bash
npm run lint
```

---

## 📦 Building for Production

### **Android APK**
```bash
npm run build:android
# Output: android/app/build/outputs/apk/release/app-release.apk
```

### **iOS Archive**
```bash
npm run build:ios
# Open Xcode to create archive and upload to App Store
```

---

## 🔧 Troubleshooting

### **Common Issues**

**1. WebSocket Connection Failed**
- Check server URL in Settings
- Ensure backend is running
- Verify firewall settings
- Use correct emulator IP (10.0.2.2 for Android)

**2. Metro Bundler Issues**
```bash
npm start -- --reset-cache
```

**3. Build Errors**
```bash
cd android && ./gradlew clean
cd ios && pod install
```

**4. iOS Signing**
- Update team in Xcode
- Configure provisioning profiles

---

## 📚 Additional Documentation

### **Related Guides**
- [Backend Dashboard API](../api/dashboard/README.md)
- [WebSocket Protocol](../docs/md_docs/DASHBOARD_IMPLEMENTATION.md)
- [Main Documentation](../README.md)

### **Platform Support**
Currently supporting migration from:
- 💼 QuickBooks (Online & Desktop)
- 📊 SAGE (50, 100, 200, X3)
- 🌊 Wave Accounting
- 💳 Expensify
- 🏢 doola
- 📄 Dext (formerly Receipt Bank)

**Coming Soon**:
- Xero
- FreshBooks
- Zoho Books
- NetSuite

---

## 🤝 Contributing

This mobile app is part of the Quick2Odoo initiative. To contribute:

1. Follow React Native best practices
2. Maintain TypeScript types
3. Add tests for new features
4. Update documentation
5. Test on both Android and iOS

---

## 📄 License

Proprietary - QuickOdoo Project

---

## 🔗 Links

- **Main Repository**: https://github.com/cryptolavar-hub/Q2O
- **Backend API**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8000/dashboard

---

## 📱 Screenshots

### Dashboard
- Real-time project monitoring
- Multi-platform visualization
- Task progress tracking

### New Project
- Platform selection
- Objectives configuration
- One-tap submission

### Metrics
- System health
- Performance analytics
- Historical data

---

## ✨ Future Enhancements

### **Planned Features**
- [ ] Push notifications for project events
- [ ] Dark mode support
- [ ] Offline mode with queue
- [ ] Project history view
- [ ] Export reports to PDF
- [ ] Biometric authentication
- [ ] Multi-language support
- [ ] Tablet-optimized layouts

---

**Version**: 1.0.0  
**Last Updated**: November 2025  
**Platform**: Android 5.0+, iOS 12.0+

