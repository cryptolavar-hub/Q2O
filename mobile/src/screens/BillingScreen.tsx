import React, { useState, useEffect } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  Alert,
  Linking
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  RadioButton,
  Text,
  Chip,
  Divider,
  ActivityIndicator,
  Surface
} from 'react-native-paper';
import { useTheme } from './src/services/ThemeContext';
import ApiService from '../services/ApiService';

interface PricingTier {
  tier: string;
  base_price: number;
  years_included: string;
  records_included: string;
  price_per_1000_extra: number;
  best_for: string;
  features: string[];
}

interface PricingEstimate {
  base_price: number;
  data_volume_fee: number;
  platform_complexity_fee: number;
  years_multiplier: number;
  subtotal: number;
  tax: number;
  total: number;
  tier: string;
  pricing_details: {
    years_of_data: number;
    total_records: number;
    platform: string;
    entity_breakdown: Record<string, number>;
  };
}

export default function BillingScreen({ route, navigation }: any) {
  const { theme } = useTheme();
  const [pricingTiers, setPricingTiers] = useState<PricingTier[]>([]);
  const [selectedTier, setSelectedTier] = useState<string>('professional');
  const [yearsOfData, setYearsOfData] = useState<number>(5);
  const [platform, setPlatform] = useState<string>('QuickBooks Online');
  const [estimate, setEstimate] = useState<PricingEstimate | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzingData, setAnalyzingData] = useState(false);

  // Available platforms
  const platforms = [
    'QuickBooks Online',
    'QuickBooks Desktop',
    'SAGE 50',
    'SAGE 100',
    'SAGE 200',
    'Wave',
    'Expensify',
    'doola',
    'Dext'
  ];

  // Years options
  const yearsOptions = [1, 2, 3, 5, 7, 10, 15, 20];

  useEffect(() => {
    loadPricingTiers();
  }, []);

  useEffect(() => {
    // Auto-calculate estimate when selections change
    if (platform && yearsOfData) {
      calculateEstimate();
    }
  }, [platform, yearsOfData]);

  const loadPricingTiers = async () => {
    try {
      const tiers = await ApiService.getPricingTiers();
      setPricingTiers(tiers);
    } catch (error) {
      console.error('Error loading pricing tiers:', error);
    }
  };

  const calculateEstimate = async () => {
    setLoading(true);
    try {
      const estimateData = await ApiService.estimateMigrationCost({
        platform_name: platform,
        years_of_data: yearsOfData,
        estimated_records: null, // Let API estimate
        tax_rate: 0.0
      });
      
      setEstimate(estimateData);
      setSelectedTier(estimateData.tier);
    } catch (error) {
      console.error('Error calculating estimate:', error);
      Alert.alert('Error', 'Failed to calculate pricing estimate');
    } finally {
      setLoading(false);
    }
  };

  const analyzeActualDataVolume = async () => {
    setAnalyzingData(true);
    Alert.alert(
      'Connect to Platform',
      'To analyze actual data volume, we need to connect to your accounting platform. This will provide accurate pricing.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Connect',
          onPress: async () => {
            try {
              // TODO: Open OAuth flow or credential input
              // For now, show that it's coming
              Alert.alert('Coming Soon', 'Platform connection for live analysis will be available in next update.');
            } catch (error) {
              Alert.alert('Error', 'Failed to analyze data volume');
            } finally {
              setAnalyzingData(false);
            }
          }
        }
      ]
    );
    setAnalyzingData(false);
  };

  const proceedToCheckout = async () => {
    if (!estimate) {
      Alert.alert('Error', 'Please wait for pricing calculation');
      return;
    }

    Alert.alert(
      'Confirm Migration',
      `You are about to start a migration:\n\n` +
      `Platform: ${platform}\n` +
      `Years of Data: ${yearsOfData}\n` +
      `Estimated Records: ${estimate.pricing_details.total_records.toLocaleString()}\n` +
      `Total Cost: $${estimate.total.toFixed(2)}\n\n` +
      `Proceed to payment?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Pay Now',
          onPress: async () => {
            try {
              const migration_id = `MIG-${Date.now()}`;
              
              const checkout = await ApiService.createCheckoutSession({
                migration_id,
                customer_email: 'user@example.com', // TODO: Get from user profile
                pricing_data: estimate
              });
              
              // Open Stripe checkout URL
              if (checkout.url) {
                await Linking.openURL(checkout.url);
                
                // Navigate to payment status screen
                navigation.navigate('PaymentStatus', {
                  session_id: checkout.session_id,
                  migration_id
                });
              }
            } catch (error) {
              Alert.alert('Error', 'Failed to create checkout session');
            }
          }
        }
      ]
    );
  };

  return (
    <ScrollView style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <Surface style={styles.header}>
        <Title>Migration Pricing</Title>
        <Paragraph>Select your platform and data range</Paragraph>
      </Surface>

      {/* Platform Selection */}
      <Card style={styles.card}>
        <Card.Content>
          <Title>1. Select Platform</Title>
          <View style={styles.platformGrid}>
            {platforms.map((p) => (
              <Chip
                key={p}
                selected={platform === p}
                onPress={() => setPlatform(p)}
                style={styles.platformChip}
              >
                {p}
              </Chip>
            ))}
          </View>
        </Card.Content>
      </Card>

      {/* Years Selection */}
      <Card style={styles.card}>
        <Card.Content>
          <Title>2. Years of Historical Data</Title>
          <Paragraph>How many years of data do you want to migrate?</Paragraph>
          
          <View style={styles.yearsGrid}>
            {yearsOptions.map((years) => (
              <Chip
                key={years}
                selected={yearsOfData === years}
                onPress={() => setYearsOfData(years)}
                style={styles.yearsChip}
                mode={yearsOfData === years ? 'flat' : 'outlined'}
              >
                {years} {years === 1 ? 'year' : 'years'}
              </Chip>
            ))}
          </View>

          <Text style={styles.helpText}>
            More years = more historical data = higher migration complexity
          </Text>
        </Card.Content>
      </Card>

      {/* Pricing Estimate */}
      {loading ? (
        <Card style={styles.card}>
          <Card.Content>
            <ActivityIndicator size="large" />
            <Text style={styles.loadingText}>Calculating pricing...</Text>
          </Card.Content>
        </Card>
      ) : estimate ? (
        <Card style={styles.card}>
          <Card.Content>
            <Title>Pricing Estimate</Title>
            
            <View style={styles.pricingRow}>
              <Text>Tier:</Text>
              <Chip mode="outlined">{estimate.tier.toUpperCase()}</Chip>
            </View>

            <Divider style={styles.divider} />

            <View style={styles.pricingRow}>
              <Text>Base Price:</Text>
              <Text>${estimate.base_price.toFixed(2)}</Text>
            </View>

            <View style={styles.pricingRow}>
              <Text>Data Volume Fee:</Text>
              <Text>${estimate.data_volume_fee.toFixed(2)}</Text>
            </View>

            <View style={styles.pricingRow}>
              <Text>Platform Complexity:</Text>
              <Text>${estimate.platform_complexity_fee.toFixed(2)}</Text>
            </View>

            <View style={styles.pricingRow}>
              <Text>Years Multiplier:</Text>
              <Text>${estimate.years_multiplier.toFixed(2)}</Text>
            </View>

            <Divider style={styles.divider} />

            <View style={styles.pricingRow}>
              <Text style={styles.boldText}>Subtotal:</Text>
              <Text style={styles.boldText}>${estimate.subtotal.toFixed(2)}</Text>
            </View>

            {estimate.tax > 0 && (
              <View style={styles.pricingRow}>
                <Text>Tax:</Text>
                <Text>${estimate.tax.toFixed(2)}</Text>
              </View>
            )}

            <View style={[styles.pricingRow, styles.totalRow]}>
              <Text style={styles.totalText}>TOTAL:</Text>
              <Text style={styles.totalAmount}>${estimate.total.toFixed(2)}</Text>
            </View>

            <Divider style={styles.divider} />

            {/* Data Volume Details */}
            <Title style={styles.sectionTitle}>Migration Details</Title>
            
            <View style={styles.detailRow}>
              <Text>Platform:</Text>
              <Text style={styles.detailValue}>{estimate.pricing_details.platform}</Text>
            </View>

            <View style={styles.detailRow}>
              <Text>Years of Data:</Text>
              <Text style={styles.detailValue}>{estimate.pricing_details.years_of_data} years</Text>
            </View>

            <View style={styles.detailRow}>
              <Text>Estimated Records:</Text>
              <Text style={styles.detailValue}>
                {estimate.pricing_details.total_records.toLocaleString()}
              </Text>
            </View>

            {/* Entity Breakdown */}
            {estimate.pricing_details.entity_breakdown && (
              <>
                <Title style={styles.sectionTitle}>Entity Breakdown</Title>
                {Object.entries(estimate.pricing_details.entity_breakdown).map(([entity, count]) => (
                  <View key={entity} style={styles.entityRow}>
                    <Text style={styles.entityName}>{entity}:</Text>
                    <Text style={styles.entityCount}>{count.toLocaleString()}</Text>
                  </View>
                ))}
              </>
            )}
          </Card.Content>

          <Card.Actions>
            <Button
              mode="outlined"
              onPress={analyzeActualDataVolume}
              loading={analyzingData}
              disabled={analyzingData}
            >
              Analyze Actual Data
            </Button>
            
            <Button
              mode="contained"
              onPress={proceedToCheckout}
              style={styles.checkoutButton}
            >
              Proceed to Payment
            </Button>
          </Card.Actions>
        </Card>
      ) : null}

      {/* Pricing Tiers Reference */}
      <Card style={styles.card}>
        <Card.Content>
          <Title>Pricing Tiers</Title>
          
          {pricingTiers.map((tier) => (
            <View key={tier.tier} style={styles.tierCard}>
              <View style={styles.tierHeader}>
                <Text style={styles.tierName}>{tier.tier}</Text>
                <Text style={styles.tierPrice}>${tier.base_price}</Text>
              </View>
              
              <Text style={styles.tierYears}>{tier.years_included}</Text>
              <Text style={styles.tierRecords}>{tier.records_included}</Text>
              <Text style={styles.tierBestFor}>Best for: {tier.best_for}</Text>
              
              <Divider style={styles.divider} />
              
              {tier.features.map((feature, idx) => (
                <Text key={idx} style={styles.feature}>✓ {feature}</Text>
              ))}
            </View>
          ))}
        </Card.Content>
      </Card>

      <View style={styles.bottomSpacer} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  header: {
    padding: 16,
    elevation: 2,
  },
  card: {
    margin: 16,
    marginBottom: 8,
  },
  platformGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
  },
  platformChip: {
    margin: 4,
  },
  yearsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 12,
  },
  yearsChip: {
    margin: 4,
  },
  helpText: {
    marginTop: 12,
    fontSize: 12,
    opacity: 0.7,
  },
  loadingText: {
    textAlign: 'center',
    marginTop: 16,
  },
  pricingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 6,
  },
  divider: {
    marginVertical: 12,
  },
  boldText: {
    fontWeight: 'bold',
  },
  totalRow: {
    marginTop: 8,
    paddingVertical: 8,
  },
  totalText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  totalAmount: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  sectionTitle: {
    fontSize: 16,
    marginTop: 16,
    marginBottom: 8,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 4,
  },
  detailValue: {
    fontWeight: '600',
  },
  entityRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginVertical: 2,
    paddingLeft: 12,
  },
  entityName: {
    fontSize: 13,
    textTransform: 'capitalize',
  },
  entityCount: {
    fontSize: 13,
    fontWeight: '500',
  },
  checkoutButton: {
    marginLeft: 8,
  },
  tierCard: {
    marginVertical: 12,
    padding: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
  },
  tierHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  tierName: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  tierPrice: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#2196F3',
  },
  tierYears: {
    fontSize: 14,
    marginTop: 4,
  },
  tierRecords: {
    fontSize: 14,
  },
  tierBestFor: {
    fontSize: 13,
    fontStyle: 'italic',
    marginTop: 4,
  },
  feature: {
    fontSize: 13,
    marginVertical: 2,
  },
  bottomSpacer: {
    height: 40,
  },
});

