/**
 * Connection Status Component
 */

import React from 'react';
import { View, StyleSheet } from 'react-native';
import { Banner } from 'react-native-paper';

interface ConnectionStatusProps {
  connected: boolean;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ connected }) => {
  return (
    <Banner
      visible={true}
      icon={connected ? 'wifi' : 'wifi-off'}
      style={[styles.banner, connected ? styles.connected : styles.disconnected]}
    >
      {connected ? 'Connected to Dashboard' : 'Disconnected'}
    </Banner>
  );
};

const styles = StyleSheet.create({
  banner: { marginBottom: 8 },
  connected: { backgroundColor: '#c8e6c9' },
  disconnected: { backgroundColor: '#ffcdd2' },
});

export default ConnectionStatus;

