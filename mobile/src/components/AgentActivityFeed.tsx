/**
 * Agent Activity Feed Component
 */

import React from 'react';
import { View, StyleSheet } from 'react-native';
import { List, Text } from 'react-native-paper';
import { formatDistance } from 'date-fns';

interface AgentActivityFeedProps {
  activities: any[];
}

const AgentActivityFeed: React.FC<AgentActivityFeedProps> = ({ activities }) => {
  return (
    <View style={styles.container}>
      {activities.map((activity, index) => (
        <List.Item
          key={index}
          title={activity.message || activity.type}
          description={activity.timestamp ? formatDistance(new Date(activity.timestamp), new Date(), { addSuffix: true }) : 'Just now'}
          left={props => <List.Icon {...props} icon="robot" />}
          style={styles.item}
        />
      ))}
      {activities.length === 0 && (
        <Text style={styles.empty}>No recent activity</Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {},
  item: { paddingVertical: 4 },
  empty: { textAlign: 'center', padding: 16, color: '#999' },
});

export default AgentActivityFeed;

