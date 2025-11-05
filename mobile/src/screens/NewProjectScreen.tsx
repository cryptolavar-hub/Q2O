/**
 * New Project Screen
 * Initiate new multi-platform Odoo migration projects
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  Alert,
} from 'react-native';
import {
  TextInput,
  Button,
  Chip,
  Title,
  Paragraph,
  Card,
  HelperText,
  ActivityIndicator,
} from 'react-native-paper';
import ApiService, { ProjectConfig } from '../services/ApiService';
import { useDashboard } from '../services/DashboardContext';

const NewProjectScreen = ({ navigation }: any) => {
  const { state } = useDashboard();
  const [projectDescription, setProjectDescription] = useState('');
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);
  const [objectives, setObjectives] = useState<string[]>(['']);
  const [availablePlatforms, setAvailablePlatforms] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadAvailablePlatforms();
  }, []);

  const loadAvailablePlatforms = async () => {
    try {
      setLoading(true);
      const platforms = await ApiService.getAvailablePlatforms();
      setAvailablePlatforms(platforms);
    } catch (error: any) {
      Alert.alert('Error', 'Failed to load available platforms');
    } finally {
      setLoading(false);
    }
  };

  const togglePlatform = (platform: string) => {
    if (selectedPlatforms.includes(platform)) {
      setSelectedPlatforms(selectedPlatforms.filter(p => p !== platform));
    } else {
      setSelectedPlatforms([...selectedPlatforms, platform]);
    }
  };

  const addObjective = () => {
    setObjectives([...objectives, '']);
  };

  const updateObjective = (index: number, value: string) => {
    const newObjectives = [...objectives];
    newObjectives[index] = value;
    setObjectives(newObjectives);
  };

  const removeObjective = (index: number) => {
    if (objectives.length > 1) {
      setObjectives(objectives.filter((_, i) => i !== index));
    }
  };

  const validateForm = (): boolean => {
    if (!projectDescription.trim()) {
      Alert.alert('Validation Error', 'Please enter a project description');
      return false;
    }

    if (selectedPlatforms.length === 0) {
      Alert.alert('Validation Error', 'Please select at least one target platform');
      return false;
    }

    const validObjectives = objectives.filter(obj => obj.trim());
    if (validObjectives.length === 0) {
      Alert.alert('Validation Error', 'Please enter at least one objective');
      return false;
    }

    return true;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    if (!state.connected) {
      Alert.alert(
        'Not Connected',
        'Please connect to the server in Settings before starting a project.',
        [
          { text: 'OK', style: 'cancel' },
          { text: 'Settings', onPress: () => navigation.navigate('Settings') },
        ]
      );
      return;
    }

    try {
      setSubmitting(true);

      const config: ProjectConfig = {
        project_description: projectDescription.trim(),
        platforms: selectedPlatforms,
        objectives: objectives.filter(obj => obj.trim()),
      };

      await ApiService.startProject(config);

      Alert.alert(
        'Success',
        'Project started successfully! Monitor progress in the Dashboard.',
        [
          {
            text: 'View Dashboard',
            onPress: () => navigation.navigate('Dashboard'),
          },
        ]
      );

      // Reset form
      setProjectDescription('');
      setSelectedPlatforms([]);
      setObjectives(['']);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to start project');
    } finally {
      setSubmitting(false);
    }
  };

  const loadExample = () => {
    setProjectDescription('Multi-Platform to Odoo v18 Migration SaaS');
    setSelectedPlatforms(['QuickBooks', 'SAGE', 'Wave']);
    setObjectives([
      'OAuth authentication for multiple platforms',
      'Cross-platform data synchronization',
      'Unified frontend dashboard',
      'Stripe billing integration',
    ]);
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196F3" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Start New Project</Title>
          <Paragraph>
            Configure and launch a new multi-platform Odoo migration project
          </Paragraph>

          {/* Project Description */}
          <TextInput
            label="Project Description *"
            value={projectDescription}
            onChangeText={setProjectDescription}
            mode="outlined"
            style={styles.input}
            placeholder="E.g., Multi-Platform to Odoo v18 Migration"
            multiline
            numberOfLines={2}
          />
          <HelperText type="info">
            Describe the high-level goal of this migration project
          </HelperText>

          {/* Platform Selection */}
          <Title style={styles.sectionTitle}>Target Platforms *</Title>
          <Paragraph style={styles.sectionDesc}>
            Select accounting platforms to migrate from:
          </Paragraph>
          <View style={styles.chipsContainer}>
            {availablePlatforms.map((platform, index) => (
              <Chip
                key={index}
                selected={selectedPlatforms.includes(platform)}
                onPress={() => togglePlatform(platform)}
                style={styles.chip}
                icon={selectedPlatforms.includes(platform) ? 'check' : 'office-building'}
              >
                {platform}
              </Chip>
            ))}
          </View>
          <HelperText type="info">
            {selectedPlatforms.length} platform(s) selected
          </HelperText>

          {/* Objectives */}
          <Title style={styles.sectionTitle}>Project Objectives *</Title>
          <Paragraph style={styles.sectionDesc}>
            Define specific goals and features to implement:
          </Paragraph>
          
          {objectives.map((objective, index) => (
            <View key={index} style={styles.objectiveRow}>
              <TextInput
                label={`Objective ${index + 1}`}
                value={objective}
                onChangeText={(text) => updateObjective(index, text)}
                mode="outlined"
                style={styles.objectiveInput}
                placeholder="E.g., OAuth authentication"
                right={
                  objectives.length > 1 ? (
                    <TextInput.Icon
                      icon="close"
                      onPress={() => removeObjective(index)}
                    />
                  ) : undefined
                }
              />
            </View>
          ))}

          <Button
            mode="outlined"
            onPress={addObjective}
            style={styles.addButton}
            icon="plus"
          >
            Add Objective
          </Button>

          {/* Actions */}
          <View style={styles.actionsContainer}>
            <Button
              mode="outlined"
              onPress={loadExample}
              style={styles.exampleButton}
              disabled={submitting}
            >
              Load Example
            </Button>

            <Button
              mode="contained"
              onPress={handleSubmit}
              style={styles.submitButton}
              loading={submitting}
              disabled={submitting}
              icon="rocket-launch"
            >
              Start Project
            </Button>
          </View>

          {submitting && (
            <HelperText type="info" style={styles.submittingText}>
              Initiating project... This may take a few moments.
            </HelperText>
          )}
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  card: {
    margin: 16,
  },
  input: {
    marginTop: 16,
  },
  sectionTitle: {
    fontSize: 18,
    marginTop: 24,
    marginBottom: 8,
  },
  sectionDesc: {
    fontSize: 13,
    color: '#666',
    marginBottom: 12,
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
  objectiveRow: {
    marginBottom: 12,
  },
  objectiveInput: {
    flex: 1,
  },
  addButton: {
    marginTop: 8,
    marginBottom: 24,
  },
  actionsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 24,
  },
  exampleButton: {
    flex: 1,
    marginRight: 8,
  },
  submitButton: {
    flex: 1,
    marginLeft: 8,
  },
  submittingText: {
    marginTop: 12,
    textAlign: 'center',
  },
});

export default NewProjectScreen;

