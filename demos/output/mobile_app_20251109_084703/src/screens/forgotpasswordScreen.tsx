import React from 'react';
import {View, Text, StyleSheet} from 'react-native';

export default function ForgotpasswordScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>ForgotPassword</Text>
      <Text style={styles.subtitle}>Screen implementation goes here</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
  },
});
