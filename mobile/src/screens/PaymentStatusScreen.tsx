import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  ScrollView
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  ActivityIndicator,
  Text,
  Surface
} from 'react-native-paper';
import { useTheme } from '../services/ThemeContext';
import ApiService from '../services/ApiService';

interface PaymentStatus {
  migration_id: string;
  payment_status: string;
  status: string;
  amount_total: number;
  customer_email: string;
  tier: string;
  paid: boolean;
}

export default function PaymentStatusScreen({ route, navigation }: any) {
  const { theme } = useTheme();
  const { session_id, migration_id } = route.params;
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkPaymentStatus();
    
    // Poll every 3 seconds until payment is confirmed
    const interval = setInterval(checkPaymentStatus, 3000);
    
    return () => clearInterval(interval);
  }, [session_id]);

  const checkPaymentStatus = async () => {
    try {
      const status = await ApiService.checkPaymentStatus(session_id);
      setPaymentStatus(status);
      setLoading(false);
      
      // Stop polling if paid
      if (status.paid) {
        // Navigate to migration start screen
        setTimeout(() => {
          navigation.navigate('MigrationProgress', {
            migration_id: status.migration_id
          });
        }, 2000);
      }
    } catch (err) {
      setError('Failed to check payment status');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <Surface style={styles.centerCard}>
          <ActivityIndicator size="large" />
          <Text style={styles.loadingText}>Checking payment status...</Text>
        </Surface>
      </View>
    );
  }

  if (error) {
    return (
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <Card style={styles.card}>
          <Card.Content>
            <Title>Error</Title>
            <Paragraph>{error}</Paragraph>
          </Card.Content>
          <Card.Actions>
            <Button onPress={() => navigation.goBack()}>Go Back</Button>
          </Card.Actions>
        </Card>
      </View>
    );
  }

  const isPaid = paymentStatus?.paid;

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <Surface style={styles.statusCard}>
        {isPaid ? (
          <View style={styles.successContainer}>
            <Text style={styles.successIcon}>✓</Text>
            <Title style={styles.successTitle}>Payment Successful!</Title>
            <Paragraph style={styles.successText}>
              Your migration has been paid and will start shortly.
            </Paragraph>
          </View>
        ) : (
          <View style={styles.pendingContainer}>
            <ActivityIndicator size="large" color="#FFA726" />
            <Title style={styles.pendingTitle}>Payment Pending</Title>
            <Paragraph style={styles.pendingText}>
              Waiting for payment confirmation...
            </Paragraph>
          </View>
        )}
      </Surface>

      {paymentStatus && (
        <Card style={styles.card}>
          <Card.Content>
            <Title>Migration Details</Title>
            
            <View style={styles.detailRow}>
              <Text>Migration ID:</Text>
              <Text style={styles.detailValue}>{paymentStatus.migration_id}</Text>
            </View>

            <View style={styles.detailRow}>
              <Text>Tier:</Text>
              <Text style={styles.detailValue}>{paymentStatus.tier?.toUpperCase()}</Text>
            </View>

            <View style={styles.detailRow}>
              <Text>Amount:</Text>
              <Text style={styles.detailValue}>${paymentStatus.amount_total.toFixed(2)}</Text>
            </View>

            <View style={styles.detailRow}>
              <Text>Status:</Text>
              <Text style={[
                styles.detailValue,
                { color: isPaid ? '#4CAF50' : '#FFA726' }
              ]}>
                {paymentStatus.payment_status?.toUpperCase()}
              </Text>
            </View>

            <View style={styles.detailRow}>
              <Text>Email:</Text>
              <Text style={styles.detailValue}>{paymentStatus.customer_email}</Text>
            </View>
          </Card.Content>
        </Card>
      )}

      {isPaid && (
        <Card style={styles.card}>
          <Card.Content>
            <Title>Next Steps</Title>
            <Paragraph>
              Your migration will start automatically. You can monitor progress in real-time from the Dashboard.
            </Paragraph>
          </Card.Content>
          <Card.Actions>
            <Button
              mode="contained"
              onPress={() => navigation.navigate('Dashboard')}
            >
              Go to Dashboard
            </Button>
          </Card.Actions>
        </Card>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centerCard: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  loadingText: {
    marginTop: 16,
  },
  card: {
    margin: 16,
  },
  statusCard: {
    margin: 16,
    padding: 24,
    elevation: 4,
    borderRadius: 12,
  },
  successContainer: {
    alignItems: 'center',
  },
  successIcon: {
    fontSize: 64,
    color: '#4CAF50',
    marginBottom: 16,
  },
  successTitle: {
    color: '#4CAF50',
    marginBottom: 8,
  },
  successText: {
    textAlign: 'center',
  },
  pendingContainer: {
    alignItems: 'center',
  },
  pendingTitle: {
    color: '#FFA726',
    marginTop: 16,
    marginBottom: 8,
  },
  pendingText: {
    textAlign: 'center',
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 6,
  },
  detailValue: {
    fontWeight: '600',
  },
});

