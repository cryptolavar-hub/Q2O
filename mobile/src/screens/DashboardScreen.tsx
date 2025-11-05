/**
 * Main Dashboard Screen
 * Real-time monitoring of projects, tasks, and agent activity
 */

import React, { useEffect } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  RefreshControl,
  Alert,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Chip,
  ProgressBar,
  ActivityIndicator,
  Button,
  Surface,
  Text,
  Badge,
} from 'react-native-paper';
import { useDashboard } from '../services/DashboardContext';
import ConnectionStatus from '../components/ConnectionStatus';
import TaskCard from '../components/TaskCard';
import AgentActivityFeed from '../components/AgentActivityFeed';

const DashboardScreen = ({ navigation }: any) => {
  const { state, refreshMetrics } = useDashboard();
  const [refreshing, setRefreshing] = React.useState(false);

  useEffect(() => {
    if (!state.connected) {
      // Show connection prompt
      Alert.alert(
        'Not Connected',
        'Please configure server connection in Settings',
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Settings', onPress: () => navigation.navigate('Settings') },
        ]
      );
    }
  }, [state.connected]);

  const onRefresh = async () => {
    setRefreshing(true);
    await refreshMetrics();
    setRefreshing(false);
  };

  const getTaskStatistics = () => {
    const total = state.tasks.length;
    const completed = state.tasks.filter(t => t.status === 'completed').length;
    const inProgress = state.tasks.filter(t => t.status === 'in_progress').length;
    const failed = state.tasks.filter(t => t.status === 'failed').length;
    
    return { total, completed, inProgress, failed };
  };

  const stats = getTaskStatistics();

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Connection Status */}
      <ConnectionStatus connected={state.connected} />

      {/* Current Project Card */}
      {state.currentProject && (
        <Card style={styles.card}>
          <Card.Content>
            <Title>Current Project</Title>
            <Paragraph style={styles.projectDesc}>
              {state.currentProject.project_description}
            </Paragraph>
            
            {state.currentProject.platforms && state.currentProject.platforms.length > 0 && (
              <View style={styles.platformsContainer}>
                <Text style={styles.label}>Target Platforms:</Text>
                <View style={styles.chipsContainer}>
                  {state.currentProject.platforms.map((platform, index) => (
                    <Chip
                      key={index}
                      mode="outlined"
                      style={styles.chip}
                      icon="office-building"
                    >
                      {platform}
                    </Chip>
                  ))}
                </View>
              </View>
            )}

            <View style={styles.objectivesContainer}>
              <Text style={styles.label}>Objectives ({state.currentProject.objectives.length}):</Text>
              {state.currentProject.objectives.slice(0, 3).map((obj, index) => (
                <Text key={index} style={styles.objective}>• {obj}</Text>
              ))}
              {state.currentProject.objectives.length > 3 && (
                <Text style={styles.moreText}>
                  +{state.currentProject.objectives.length - 3} more...
                </Text>
              )}
            </View>

            <Button
              mode="contained"
              onPress={() => navigation.navigate('ProjectDetails', { project: state.currentProject })}
              style={styles.detailsButton}
            >
              View Details
            </Button>
          </Card.Content>
        </Card>
      )}

      {/* Task Statistics */}
      {state.tasks.length > 0 && (
        <Card style={styles.card}>
          <Card.Content>
            <Title>Task Statistics</Title>
            
            <View style={styles.statsRow}>
              <Surface style={[styles.statBox, { backgroundColor: '#e3f2fd' }]}>
                <Text style={styles.statNumber}>{stats.total}</Text>
                <Text style={styles.statLabel}>Total</Text>
              </Surface>
              
              <Surface style={[styles.statBox, { backgroundColor: '#c8e6c9' }]}>
                <Text style={[styles.statNumber, { color: '#4caf50' }]}>{stats.completed}</Text>
                <Text style={styles.statLabel}>Completed</Text>
              </Surface>
              
              <Surface style={[styles.statBox, { backgroundColor: '#fff9c4' }]}>
                <Text style={[styles.statNumber, { color: '#ff9800' }]}>{stats.inProgress}</Text>
                <Text style={styles.statLabel}>In Progress</Text>
              </Surface>
              
              {stats.failed > 0 && (
                <Surface style={[styles.statBox, { backgroundColor: '#ffcdd2' }]}>
                  <Text style={[styles.statNumber, { color: '#f44336' }]}>{stats.failed}</Text>
                  <Text style={styles.statLabel}>Failed</Text>
                </Surface>
              )}
            </View>

            {/* Overall Progress */}
            <View style={styles.progressContainer}>
              <Text style={styles.progressLabel}>
                Overall Progress: {stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0}%
              </Text>
              <ProgressBar
                progress={stats.total > 0 ? stats.completed / stats.total : 0}
                color="#2196F3"
                style={styles.progressBar}
              />
            </View>
          </Card.Content>
        </Card>
      )}

      {/* Recent Tasks */}
      {state.tasks.length > 0 && (
        <Card style={styles.card}>
          <Card.Content>
            <Title>Recent Tasks</Title>
            {state.tasks.slice(0, 5).map((task, index) => (
              <TaskCard key={index} task={task} />
            ))}
            {state.tasks.length > 5 && (
              <Text style={styles.moreText}>
                +{state.tasks.length - 5} more tasks...
              </Text>
            )}
          </Card.Content>
        </Card>
      )}

      {/* Agent Activity Feed */}
      {state.agentActivity.length > 0 && (
        <Card style={styles.card}>
          <Card.Content>
            <Title>Agent Activity</Title>
            <AgentActivityFeed activities={state.agentActivity.slice(0, 10)} />
          </Card.Content>
        </Card>
      )}

      {/* No Active Project */}
      {!state.currentProject && state.connected && (
        <Card style={styles.card}>
          <Card.Content>
            <Title>No Active Project</Title>
            <Paragraph>Start a new project to see real-time monitoring.</Paragraph>
            <Button
              mode="contained"
              onPress={() => navigation.navigate('New Project')}
              style={styles.detailsButton}
              icon="plus-circle"
            >
              Start New Project
            </Button>
          </Card.Content>
        </Card>
      )}

      {state.loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#2196F3" />
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  card: {
    margin: 16,
    marginBottom: 8,
  },
  projectDesc: {
    marginVertical: 8,
    fontSize: 14,
  },
  platformsContainer: {
    marginTop: 12,
  },
  label: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#666',
    marginBottom: 8,
  },
  chipsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginBottom: 8,
  },
  chip: {
    marginRight: 8,
    marginBottom: 8,
  },
  objectivesContainer: {
    marginTop: 12,
  },
  objective: {
    marginLeft: 8,
    marginVertical: 2,
    fontSize: 13,
  },
  moreText: {
    marginTop: 4,
    fontStyle: 'italic',
    color: '#666',
  },
  detailsButton: {
    marginTop: 16,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 12,
  },
  statBox: {
    flex: 1,
    padding: 12,
    margin: 4,
    borderRadius: 8,
    alignItems: 'center',
  },
  statNumber: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2196F3',
  },
  statLabel: {
    fontSize: 11,
    color: '#666',
    marginTop: 4,
  },
  progressContainer: {
    marginTop: 12,
  },
  progressLabel: {
    fontSize: 13,
    marginBottom: 8,
    fontWeight: '500',
  },
  progressBar: {
    height: 8,
    borderRadius: 4,
  },
  loadingContainer: {
    padding: 32,
    alignItems: 'center',
  },
});

export default DashboardScreen;

