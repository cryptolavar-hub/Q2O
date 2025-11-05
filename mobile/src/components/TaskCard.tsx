/**
 * Task Card Component
 */

import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Card, Paragraph, Chip, ProgressBar } from 'react-native-paper';
import { TaskUpdate } from '../services/DashboardWebSocket';

interface TaskCardProps {
  task: TaskUpdate;
}

const TaskCard: React.FC<TaskCardProps> = ({ task }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#4caf50';
      case 'in_progress': return '#ff9800';
      case 'failed': return '#f44336';
      default: return '#757575';
    }
  };

  return (
    <Card style={styles.card}>
      <Card.Content>
        <View style={styles.header}>
          <Chip mode="outlined" style={{ borderColor: getStatusColor(task.status) }}>
            {task.agent_type}
          </Chip>
          <Chip textStyle={{ color: getStatusColor(task.status) }}>
            {task.status}
          </Chip>
        </View>
        {task.message && <Paragraph style={styles.message}>{task.message}</Paragraph>}
        {task.progress > 0 && (
          <ProgressBar progress={task.progress / 100} color={getStatusColor(task.status)} style={styles.progress} />
        )}
      </Card.Content>
    </Card>
  );
};

const styles = StyleSheet.create({
  card: { marginVertical: 4 },
  header: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 },
  message: { fontSize: 13, marginTop: 4 },
  progress: { marginTop: 8, height: 6, borderRadius: 3 },
});

export default TaskCard;

