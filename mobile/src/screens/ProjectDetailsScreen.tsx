/**
 * Project Details Screen
 */

import React from 'react';
import { ScrollView, StyleSheet } from 'react-native';
import { Card, Title, Paragraph, Chip, List } from 'react-native-paper';

const ProjectDetailsScreen = ({ route }: any) => {
  const { project } = route.params;

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Project Details</Title>
          <Paragraph>{project.project_description}</Paragraph>
          
          <List.Section>
            <List.Subheader>Target Platforms</List.Subheader>
            {project.platforms?.map((platform: string, index: number) => (
              <Chip key={index} style={styles.chip}>{platform}</Chip>
            ))}
          </List.Section>

          <List.Section>
            <List.Subheader>Objectives</List.Subheader>
            {project.objectives?.map((obj: string, index: number) => (
              <List.Item key={index} title={obj} left={props => <List.Icon {...props} icon="checkbox-marked-circle" />} />
            ))}
          </List.Section>
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  card: { margin: 16 },
  chip: { marginRight: 8, marginBottom: 8 },
});

export default ProjectDetailsScreen;

