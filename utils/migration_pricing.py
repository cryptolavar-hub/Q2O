"""
Migration Pricing Engine - Data-volume-based pricing for migrations.
Calculates costs based on years of data, record count, and platform complexity.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PricingTier(Enum):
    """Migration pricing tiers."""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class PlatformComplexity(Enum):
    """Platform integration complexity."""
    SIMPLE = 1.0      # Wave, Expensify (simple APIs)
    MODERATE = 1.3    # QuickBooks Online, Dext
    COMPLEX = 1.5     # SAGE, QuickBooks Desktop
    ENTERPRISE = 2.0  # NetSuite, SAP


@dataclass
class DataVolumeAnalysis:
    """Analysis of migration data volume."""
    years_of_data: int
    total_records: int
    entity_breakdown: Dict[str, int]
    estimated_size_mb: float
    complexity_score: float
    platform_name: str
    
    def get_complexity_level(self) -> str:
        """Get human-readable complexity level."""
        if self.total_records < 5000:
            return "Small"
        elif self.total_records < 50000:
            return "Medium"
        elif self.total_records < 500000:
            return "Large"
        else:
            return "Enterprise"


@dataclass
class MigrationPricing:
    """Migration pricing breakdown."""
    base_price: float
    data_volume_fee: float
    platform_complexity_fee: float
    years_multiplier: float
    total_records_fee: float
    subtotal: float
    tax: float
    total: float
    tier: str
    
    # Breakdown for transparency
    pricing_details: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses."""
        return {
            "base_price": self.base_price,
            "data_volume_fee": self.data_volume_fee,
            "platform_complexity_fee": self.platform_complexity_fee,
            "years_multiplier": self.years_multiplier,
            "total_records_fee": self.total_records_fee,
            "subtotal": self.subtotal,
            "tax": self.tax,
            "total": self.total,
            "tier": self.tier,
            "pricing_details": self.pricing_details
        }


class MigrationPricingEngine:
    """
    Calculates migration pricing based on data volume, years, and complexity.
    Loads pricing from configurable JSON file for easy updates.
    """
    
    def __init__(self, tax_rate: float = 0.0, config_path: str = None):
        """
        Initialize pricing engine.
        
        Args:
            tax_rate: Tax rate (e.g., 0.08 for 8%)
            config_path: Path to pricing config JSON (default: config/pricing_config.json)
        """
        self.tax_rate = tax_rate
        
        # Load pricing configuration from JSON file
        if config_path is None:
            import os
            config_path = os.getenv(
                "PRICING_CONFIG_PATH",
                str(Path(__file__).parent.parent / "config" / "pricing_config.json")
            )
        
        self.config = self._load_pricing_config(config_path)
        
        # Parse config into usable structures
        self.BASE_PRICES = {}
        self.PRICE_PER_1000_RECORDS = {}
        self.tier_configs = {}
        
        for tier_key, tier_data in self.config["tiers"].items():
            # Map tier name to enum
            tier_enum = self._get_tier_enum(tier_key)
            self.BASE_PRICES[tier_enum] = tier_data["base_price"]
            self.PRICE_PER_1000_RECORDS[tier_enum] = tier_data["price_per_1000_extra_records"]
            self.tier_configs[tier_enum] = tier_data
        
        # Platform multipliers from config
        self.PLATFORM_MULTIPLIERS = self.config["platform_multipliers"]
        
        # Years multiplier rate
        self.years_multiplier_rate = self.config["years_multiplier"]["rate_per_year"]
    
    def _load_pricing_config(self, config_path: str) -> Dict:
        """Load pricing configuration from JSON file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_tier_enum(self, tier_key: str) -> PricingTier:
        """Map tier key to enum."""
        tier_map = {
            "starter": PricingTier.STARTER,
            "professional": PricingTier.PROFESSIONAL,
            "enterprise": PricingTier.ENTERPRISE,
            "custom": PricingTier.CUSTOM
        }
        return tier_map.get(tier_key.lower(), PricingTier.PROFESSIONAL)
    
    def analyze_data_volume(self, source_client: Any, years: int, 
                           platform_name: str) -> DataVolumeAnalysis:
        """
        Analyze data volume from source platform.
        
        Args:
            source_client: Source platform client (e.g., QBOFullClient)
            years: Number of years of historical data to include
            platform_name: Platform name
            
        Returns:
            Data volume analysis
        """
        logger.info(f"Analyzing data volume for {years} years from {platform_name}...")
        
        # Calculate cutoff date
        cutoff_date = (datetime.now() - timedelta(days=years * 365)).isoformat()
        
        # Extract all entities
        all_data = source_client.get_all_entities()
        
        # Count records per entity type
        entity_breakdown = {}
        total_records = 0
        
        for entity_type, entities in all_data.items():
            if not entities:
                continue
            
            # Filter by date if applicable
            filtered_entities = self._filter_by_date(entities, cutoff_date)
            count = len(filtered_entities)
            
            if count > 0:
                entity_breakdown[entity_type] = count
                total_records += count
        
        # Estimate size (rough calculation)
        estimated_size_mb = total_records * 0.05  # ~50KB per record average
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity(entity_breakdown, platform_name)
        
        return DataVolumeAnalysis(
            years_of_data=years,
            total_records=total_records,
            entity_breakdown=entity_breakdown,
            estimated_size_mb=estimated_size_mb,
            complexity_score=complexity_score,
            platform_name=platform_name
        )
    
    def _filter_by_date(self, entities: List[Dict], cutoff_date: str) -> List[Dict]:
        """Filter entities by date."""
        # Try common date fields
        date_fields = ["TxnDate", "MetaData.CreateTime", "invoice_date", "created_at", "date"]
        
        filtered = []
        for entity in entities:
            entity_date = None
            
            # Find date field
            for field in date_fields:
                if "." in field:
                    # Nested field
                    parts = field.split(".")
                    value = entity
                    for part in parts:
                        value = value.get(part, {}) if isinstance(value, dict) else None
                    entity_date = value
                else:
                    entity_date = entity.get(field)
                
                if entity_date:
                    break
            
            # Include if within date range or no date found (assume recent)
            if not entity_date or entity_date >= cutoff_date:
                filtered.append(entity)
        
        return filtered
    
    def _calculate_complexity(self, entity_breakdown: Dict[str, int], 
                             platform_name: str) -> float:
        """
        Calculate complexity score based on entity distribution.
        
        Args:
            entity_breakdown: Count of records per entity type
            platform_name: Platform name
            
        Returns:
            Complexity score (1.0 - 10.0)
        """
        score = 1.0
        
        # More entity types = higher complexity
        entity_count = len(entity_breakdown)
        score += min(entity_count * 0.1, 3.0)
        
        # Large transaction volumes increase complexity
        transaction_types = ["invoices", "bills", "journal_entries", "payments"]
        transaction_count = sum(entity_breakdown.get(t, 0) for t in transaction_types)
        
        if transaction_count > 100000:
            score += 2.0
        elif transaction_count > 50000:
            score += 1.5
        elif transaction_count > 10000:
            score += 1.0
        
        # Platform-specific multiplier
        platform_multiplier = self.PLATFORM_MULTIPLIERS.get(platform_name, 1.0)
        score *= platform_multiplier
        
        return min(score, 10.0)
    
    def calculate_pricing(self, data_volume: DataVolumeAnalysis, 
                         custom_adjustments: Optional[Dict] = None) -> MigrationPricing:
        """
        Calculate migration pricing.
        
        Args:
            data_volume: Data volume analysis
            custom_adjustments: Optional custom pricing adjustments
            
        Returns:
            Migration pricing breakdown
        """
        logger.info(f"Calculating pricing for {data_volume.total_records} records over {data_volume.years_of_data} years...")
        
        # Determine tier based on data volume
        tier = self._determine_tier(data_volume)
        
        # Base price
        base_price = self.BASE_PRICES[tier]
        
        # Calculate additional fees
        
        # 1. Data volume fee (records beyond base tier allocation)
        base_allocation = self._get_base_record_allocation(tier)
        excess_records = max(0, data_volume.total_records - base_allocation)
        records_fee = (excess_records / 1000) * self.PRICE_PER_1000_RECORDS[tier]
        
        # 2. Years multiplier (more years = more historical data complexity)
        # Use configurable rate (default 10% per year)
        years_multiplier_value = 1.0 + (data_volume.years_of_data - 1) * self.years_multiplier_rate
        years_fee = base_price * (years_multiplier_value - 1.0)
        
        # 3. Platform complexity fee
        platform_multiplier = self.PLATFORM_MULTIPLIERS.get(data_volume.platform_name, 1.0)
        platform_fee = base_price * (platform_multiplier - 1.0)
        
        # Apply custom adjustments if provided
        discount = 0.0
        surcharge = 0.0
        
        if custom_adjustments:
            discount = custom_adjustments.get("discount_percent", 0) / 100
            surcharge = custom_adjustments.get("surcharge_amount", 0)
        
        # Calculate subtotal
        subtotal = base_price + records_fee + years_fee + platform_fee + surcharge
        subtotal = subtotal * (1 - discount)
        
        # Calculate tax
        tax = subtotal * self.tax_rate
        
        # Total
        total = subtotal + tax
        
        # Pricing details for transparency
        pricing_details = {
            "tier": tier.value,
            "years_of_data": data_volume.years_of_data,
            "total_records": data_volume.total_records,
            "platform": data_volume.platform_name,
            "entity_breakdown": data_volume.entity_breakdown,
            "complexity_score": data_volume.complexity_score,
            "base_allocation_records": base_allocation,
            "excess_records": excess_records,
            "platform_multiplier": platform_multiplier,
            "years_multiplier": years_multiplier_value,
            "discount_applied": discount * 100,
            "surcharge_applied": surcharge
        }
        
        return MigrationPricing(
            base_price=base_price,
            data_volume_fee=records_fee,
            platform_complexity_fee=platform_fee,
            years_multiplier=years_fee,
            total_records_fee=records_fee,
            subtotal=subtotal,
            tax=tax,
            total=total,
            tier=tier.value,
            pricing_details=pricing_details
        )
    
    def _determine_tier(self, data_volume: DataVolumeAnalysis) -> PricingTier:
        """Determine pricing tier based on data volume."""
        records = data_volume.total_records
        years = data_volume.years_of_data
        
        # Tier logic
        if records < 5000 and years <= 2:
            return PricingTier.STARTER
        elif records < 50000 and years <= 5:
            return PricingTier.PROFESSIONAL
        elif records < 500000 and years <= 10:
            return PricingTier.ENTERPRISE
        else:
            return PricingTier.CUSTOM
    
    def _get_base_record_allocation(self, tier: PricingTier) -> int:
        """Get base record allocation for tier (before per-record fees)."""
        allocations = {
            PricingTier.STARTER: 5000,
            PricingTier.PROFESSIONAL: 50000,
            PricingTier.ENTERPRISE: 500000,
            PricingTier.CUSTOM: 1000000
        }
        return allocations[tier]
    
    def estimate_migration_cost_quick(self, platform_name: str, years: int, 
                                      estimated_records: int) -> MigrationPricing:
        """
        Quick cost estimation without connecting to source platform.
        
        Args:
            platform_name: Platform name
            years: Years of data
            estimated_records: Estimated total records
            
        Returns:
            Pricing estimate
        """
        # Create synthetic data volume
        data_volume = DataVolumeAnalysis(
            years_of_data=years,
            total_records=estimated_records,
            entity_breakdown={"estimated": estimated_records},
            estimated_size_mb=estimated_records * 0.05,
            complexity_score=5.0,  # Average
            platform_name=platform_name
        )
        
        return self.calculate_pricing(data_volume)
    
    def get_pricing_tiers_info(self) -> List[Dict]:
        """
        Get pricing tiers information for display.
        
        Returns:
            List of pricing tier details
        """
        return [
            {
                "tier": "Starter",
                "base_price": 499.00,
                "years_included": "1-2 years",
                "records_included": "Up to 5,000 records",
                "price_per_1000_extra": 5.00,
                "best_for": "Small businesses, startups",
                "features": [
                    "Full migration (all entities)",
                    "Email support",
                    "2 years historical data",
                    "Single company migration"
                ]
            },
            {
                "tier": "Professional",
                "base_price": 1499.00,
                "years_included": "3-5 years",
                "records_included": "Up to 50,000 records",
                "price_per_1000_extra": 3.00,
                "best_for": "Growing businesses",
                "features": [
                    "Full migration (all entities)",
                    "Priority email support",
                    "5 years historical data",
                    "Multiple company migration",
                    "Data validation report"
                ]
            },
            {
                "tier": "Enterprise",
                "base_price": 4999.00,
                "years_included": "6-10 years",
                "records_included": "Up to 500,000 records",
                "price_per_1000_extra": 2.00,
                "best_for": "Established enterprises",
                "features": [
                    "Full migration (all entities)",
                    "24/7 phone + email support",
                    "10 years historical data",
                    "Unlimited companies",
                    "Complete audit trail",
                    "Balance sheet validation",
                    "Dedicated migration specialist"
                ]
            },
            {
                "tier": "Custom",
                "base_price": 9999.00,
                "years_included": "10+ years",
                "records_included": "500,000+ records",
                "price_per_1000_extra": 1.50,
                "best_for": "Large enterprises, complex migrations",
                "features": [
                    "Full migration (all entities)",
                    "White-glove service",
                    "Unlimited historical data",
                    "Custom data transformations",
                    "Multi-platform consolidation",
                    "Dedicated team",
                    "Custom SLA"
                ]
            }
        ]
    
    def create_stripe_price_data(self, pricing: MigrationPricing, 
                                 migration_name: str) -> Dict:
        """
        Create Stripe price data for one-time payment.
        
        Args:
            pricing: Migration pricing
            migration_name: Migration project name
            
        Returns:
            Stripe price creation data
        """
        return {
            "unit_amount": int(pricing.total * 100),  # Stripe uses cents
            "currency": "usd",
            "product_data": {
                "name": f"Odoo Migration - {migration_name}",
                "description": f"{pricing.tier.title()} tier - {pricing.pricing_details['years_of_data']} years, {pricing.pricing_details['total_records']:,} records",
                "metadata": {
                    "tier": pricing.tier,
                    "years": pricing.pricing_details['years_of_data'],
                    "records": pricing.pricing_details['total_records'],
                    "platform": pricing.pricing_details['platform']
                }
            }
        }


def calculate_migration_cost(source_client: Any, platform_name: str, 
                            years: int, tax_rate: float = 0.0) -> MigrationPricing:
    """
    Calculate migration cost - convenience function.
    
    Args:
        source_client: Source platform client
        platform_name: Platform name
        years: Years of historical data
        tax_rate: Tax rate
        
    Returns:
        Migration pricing
    """
    engine = MigrationPricingEngine(tax_rate)
    data_volume = engine.analyze_data_volume(source_client, years, platform_name)
    return engine.calculate_pricing(data_volume)


def quick_estimate(platform_name: str, years: int, 
                  estimated_records: int, tax_rate: float = 0.0) -> MigrationPricing:
    """
    Quick cost estimate without platform connection.
    
    Args:
        platform_name: Platform name
        years: Years of data
        estimated_records: Estimated record count
        tax_rate: Tax rate
        
    Returns:
        Pricing estimate
    """
    engine = MigrationPricingEngine(tax_rate)
    return engine.estimate_migration_cost_quick(platform_name, years, estimated_records)

