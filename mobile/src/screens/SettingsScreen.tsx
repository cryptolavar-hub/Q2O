/**
 * Settings Screen - Server Configuration
 */

import React, { useState, useEffect } from 'react';
import { View, ScrollView, StyleSheet, Alert } from 'react-native';
import { Card, Title, TextInput, Button, Paragraph, Divider, List } from 'react-native-paper';
import { useDashboard } from '../services/DashboardContext';
import AsyncStorage from '@react-native-async-storage/async-storage';

const SettingsScreen = () => {
  const { state, connectToDashboard, disconnect } = useDashboard();
  const [serverUrl, setServerUrl] = useState('http://localhost:8000');
  const [connecting, setConnecting] = useState(false);

  useEffect(() => {
    loadSavedUrl();
  }, []);

  const loadSavedUrl = async () => {
    const saved = await AsyncStorage.getItem('dashboard_server_url');
    if (saved) setServerUrl(saved);
  };

  const handleConnect = async () => {
    try {
      setConnecting(true);
      await connectToDashboard(serverUrl);
      Alert.alert('Success', 'Connected to server successfully');
    } catch (error: any) {
      Alert.alert('Connection Failed', error.message);
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = () => {
    disconnect();
    Alert.alert('Disconnected', 'Connection closed');
  };

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}>
        <Card.Content>
          <Title>Server Connection</Title>
          <Paragraph style={styles.hint}>
            Configure Quick2Odoo backend server connection
          </Paragraph>
          
          <TextInput
            label="Server URL"
            value={serverUrl}
            onChangeText={setServerUrl}
            mode="outlined"
            style={styles.input}
            placeholder="http://localhost:8000"
            autoCapitalize="none"
            keyboardType="url"
          />
          
          <View style={styles.buttonRow}>
            <Button
              mode="contained"
              onPress={handleConnect}
              loading={connecting}
              disabled={connecting || state.connected}
              style={styles.button}
            >
              Connect
            </Button>
            <Button
              mode="outlined"
              onPress={handleDisconnect}
              disabled={!state.connected}
              style={styles.button}
            >
              Disconnect
            </Button>
          </View>

          <Paragraph style={styles.status}>
            Status: {state.connected ? '✅ Connected' : '❌ Disconnected'}
          </Paragraph>
        </Card.Content>
      </Card>

      <Card style={styles.card}>
        <Card.Content>
          <Title>About</Title>
          <List.Item
            title="App Version"
            description="1.0.0"
            left={props => <List.Icon {...props} icon="information" />}
          />
          <Divider />
          <List.Item
            title="Platform Support"
            description="QuickBooks, SAGE, Wave, Expensify, doola, Dext"
            left={props => <List.Icon {...props} icon="office-building" />}
          />
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  card: { margin: 16 },
  hint: { marginTop: 8, marginBottom: 16, fontSize: 13, color: '#666' },
  input: { marginBottom: 16 },
  buttonRow: { flexDirection: 'row', justifyContent: 'space-between' },
  button: { flex: 1, marginHorizontal: 4 },
  status: { marginTop: 16, fontWeight: 'bold', textAlign: 'center' },
});

export default SettingsScreen;

