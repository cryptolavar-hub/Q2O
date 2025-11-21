# GraphQL Status Page Setup

## ✅ Completed

1. **Backend Integration**
   - GraphQL router integrated into `addon_portal/api/main.py`
   - GraphQL endpoint available at `/graphql`
   - GraphiQL playground available at `GET /graphql`

2. **Frontend Setup**
   - GraphQL client library (`urql`) added to `package.json`
   - GraphQL client configured in `addon_portal/apps/tenant-portal/src/lib/graphql.ts`
   - urql Provider added to `_app.tsx`
   - Status page updated to use GraphQL queries and subscriptions

3. **Status Page Implementation**
   - Uses GraphQL queries for initial data:
     - `dashboardStats` - High-level statistics
     - `systemMetrics` - System performance metrics
   - Uses GraphQL subscriptions for real-time updates:
     - `agentActivity` - Real-time agent activity feed
     - `taskUpdates` - Real-time task status changes
     - `systemMetricsStream` - Real-time metrics updates

## 📦 Required Dependencies

The following packages need to be installed in the tenant portal:

```bash
cd addon_portal/apps/tenant-portal
npm install @urql/core @urql/next graphql subscriptions-transport-ws
```

## 🔧 Configuration

### Environment Variables (Optional)

Add to `.env` or `next.config.js`:

```env
NEXT_PUBLIC_GRAPHQL_URL=http://localhost:8080/graphql
NEXT_PUBLIC_GRAPHQL_WS_URL=ws://localhost:8080/graphql
```

Default values are already set in `graphql.ts`:
- HTTP: `http://localhost:8080/graphql`
- WebSocket: `ws://localhost:8080/graphql`

## 🚀 Next Steps

1. **Install Dependencies**
   ```bash
   cd addon_portal/apps/tenant-portal
   npm install
   ```

2. **Restart Backend API**
   - GraphQL router is now integrated
   - Endpoint: `http://localhost:8080/graphql`

3. **Test GraphQL Playground**
   - Visit: `http://localhost:8080/graphql`
   - Try the `dashboardStats` query

4. **Test Status Page**
   - Login to Tenant Portal
   - Navigate to `/status`
   - Should see real-time data from GraphQL

## 📊 GraphQL Queries Used

### Dashboard Stats Query
```graphql
query {
  dashboardStats {
    totalProjects
    activeProjects
    totalTasks
    activeTasks
    completedTasksToday
    averageSuccessRate
    recentActivities {
      agentType
      message
      timestamp
    }
  }
}
```

### System Metrics Query
```graphql
query {
  systemMetrics {
    activeAgents
    activeTasks
    cpuUsagePercent
    memoryUsagePercent
    systemHealthScore
  }
}
```

## 🔄 GraphQL Subscriptions Used

### Agent Activity Subscription
```graphql
subscription {
  agentActivity {
    agentType
    message
    timestamp
    taskId
  }
}
```

### Task Updates Subscription
```graphql
subscription {
  taskUpdates {
    id
    title
    status
    progress
  }
}
```

### System Metrics Stream Subscription
```graphql
subscription {
  systemMetricsStream(intervalSeconds: 5) {
    activeAgents
    activeTasks
    cpuUsagePercent
    memoryUsagePercent
  }
}
```

## ⚠️ Notes

- GraphQL is now the primary data source for the Status page
- Real-time updates via WebSocket subscriptions
- Falls back gracefully if GraphQL is unavailable
- Authentication token is automatically included in requests

