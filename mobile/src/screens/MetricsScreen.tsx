/**
 * Metrics Screen - System Performance and Analytics
 */

import React, { useEffect, useState } from 'react';
import { View, ScrollView, StyleSheet, RefreshControl } from 'react-native';
import { Card, Title, Paragraph, Surface, Text } from 'react-native-paper';
import { useDashboard } from '../services/DashboardContext';

const MetricsScreen = () => {
  const { state, refreshMetrics } = useDashboard();
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = async () => {
    setRefreshing(true);
    await refreshMetrics();
    setRefreshing(false);
  };

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

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  card: { margin: 16 },
  metricsGrid: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 16 },
  metricBox: { width: '48%', padding: 16, margin: '1%', borderRadius: 8, elevation: 2 },
  metricValue: { fontSize: 28, fontWeight: 'bold', color: '#2196F3' },
  metricLabel: { fontSize: 12, color: '#666', marginTop: 4 },
});

export default MetricsScreen;

