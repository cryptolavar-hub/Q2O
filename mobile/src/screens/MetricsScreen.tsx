/**
 * Metrics Screen - System Performance and Analytics
 * Tablet-optimized with responsive grid
 */

import React, { useEffect, useState } from 'react';
import { View, ScrollView, StyleSheet, RefreshControl, Dimensions } from 'react-native';
import { Card, Title, Paragraph, Surface, Text, useTheme } from 'react-native-paper';
import { useDashboard } from '../services/DashboardContext';
import ResponsiveLayout from '../utils/ResponsiveLayout';

const MetricsScreen = () => {
  const theme = useTheme();
  const { state, refreshMetrics } = useDashboard();
  const [refreshing, setRefreshing] = useState(false);
  const [deviceInfo, setDeviceInfo] = useState(ResponsiveLayout.getDeviceInfo());

  useEffect(() => {
    const updateLayout = () => {
      setDeviceInfo(ResponsiveLayout.getDeviceInfo());
    };

    const subscription = Dimensions.addEventListener('change', updateLayout);
    return () => subscription?.remove();
  }, []);

  const onRefresh = async () => {
    setRefreshing(true);
    await refreshMetrics();
    setRefreshing(false);
  };

  const columns = ResponsiveLayout.getColumns();
  const spacing = ResponsiveLayout.getSpacing();
  const metricBoxWidth = deviceInfo.isTablet 
    ? (columns === 3 ? '31%' : columns === 2 ? '48%' : '100%')
    : '48%';

  const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.colors.background },
    card: { margin: spacing * 2 },
    metricsGrid: { flexDirection: 'row', flexWrap: 'wrap', marginTop: spacing * 2 },
    metricBox: { 
      width: metricBoxWidth, 
      padding: spacing * 2, 
      margin: '1%', 
      borderRadius: 8, 
      elevation: 2,
      backgroundColor: theme.colors.surface,
    },
    metricValue: { 
      fontSize: deviceInfo.isTablet ? 32 : 28, 
      fontWeight: 'bold', 
      color: theme.colors.primary,
    },
    metricLabel: { 
      fontSize: deviceInfo.isTablet ? 14 : 12, 
      color: theme.colors.onSurfaceVariant, 
      marginTop: 4,
    },
  });

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <Card style={styles.card}>
        <Card.Content>
          <Title>System Metrics</Title>
          <View style={styles.metricsGrid}>
            <Surface style={styles.metricBox}>
              <Text style={styles.metricValue}>
                {state.metrics.active_agents || 0}
              </Text>
              <Text style={styles.metricLabel}>Active Agents</Text>
            </Surface>
            <Surface style={styles.metricBox}>
              <Text style={styles.metricValue}>
                {state.metrics.completed_tasks || 0}
              </Text>
              <Text style={styles.metricLabel}>Completed</Text>
            </Surface>
            <Surface style={styles.metricBox}>
              <Text style={styles.metricValue}>
                {state.metrics.failed_tasks || 0}
              </Text>
              <Text style={styles.metricLabel}>Failed</Text>
            </Surface>
            <Surface style={styles.metricBox}>
              <Text style={styles.metricValue}>
                {Math.round((state.metrics.cpu_usage || 0))}%
              </Text>
              <Text style={styles.metricLabel}>CPU Usage</Text>
            </Surface>
          </View>
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

export default MetricsScreen;

