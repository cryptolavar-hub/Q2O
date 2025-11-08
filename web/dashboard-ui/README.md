# Quick2Odoo Multi-Agent Dashboard UI

**Modern, real-time visual interface for monitoring AI agents**

## 🚀 Features

- ✅ Real-time WebSocket connection to Dashboard API
- ✅ Live agent activity monitoring with status indicators
- ✅ Task timeline with visual progress bars
- ✅ System metrics panel (CPU, memory, success rate)
- ✅ Modern gradient design matching Q2O branding
- ✅ Responsive layout (mobile/tablet/desktop)
- ✅ Smooth animations with Framer Motion
- ✅ Professional SaaS appearance

## 🏗️ Tech Stack

- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Modern styling
- **Framer Motion** - Smooth animations
- **Recharts** - Data visualization (optional)
- **WebSocket** - Real-time updates

## 📦 Installation

```bash
cd web/dashboard-ui
npm install
```

## 🚀 Development

```bash
npm run dev
# Opens at http://localhost:3001
```

## 🔧 Configuration

Create `.env.local`:
```bash
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/dashboard
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📊 Components

- **Header** - Gradient header with connection status
- **ProjectOverview** - Project progress and ETA
- **StatCard** - Stats with icons and trends
- **AgentCard** - Live agent status with animations
- **TaskCard** - Task progress with status badges
- **MetricsPanel** - System metrics with progress bars
- **ConnectionStatus** - Real-time connection indicator

## 🎨 Design System

**Colors**: Pink-purple gradient (matches tenant portal)  
**Typography**: System UI font stack  
**Shadows**: Soft shadows for depth  
**Animations**: Pulsing indicators for live updates  

## 🔗 API Connection

Connects to:
- WebSocket: `ws://localhost:8000/ws/dashboard`
- REST API: `http://localhost:8000/api/dashboard/*`

## 📝 Notes

- Runs on port 3001 (to avoid conflict with tenant portal on 3000)
- Auto-reconnects if WebSocket connection drops
- Graceful fallback if no data available
- Mobile-responsive design

**Created**: November 7, 2025  
**Status**: Implemented and ready for testing ✅

