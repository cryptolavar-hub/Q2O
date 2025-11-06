"""
SAGE to Odoo Migration Runner
Uses the existing Quick2Odoo migration architecture

This is what you run to actually migrate SAGE data to Odoo.
"""

import os
import logging
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import the migration components we already built
try:
    from utils.migration_orchestrator import MigrationOrchestrator
    from utils.platform_mapper import PlatformMapper
    from utils.migration_pricing import MigrationPricingEngine
except ImportError as e:
    print(f"❌ Error importing migration components: {e}")
    print("Make sure you're running from the Quick2Odoo root directory")
    sys.exit(1)

# Import SAGE client (you'll need to create api/app/clients/sage.py from the template)
try:
    from api.app.clients.sage import SAGEClient
except ImportError:
    print("❌ SAGE client not found!")
    print("You need to create: api/app/clients/sage.py")
    print("Copy from: templates/integration/sage_client.j2")
    sys.exit(1)

try:
    from api.app.clients.odoo import OdooClient
except ImportError:
    print("❌ Odoo client not found!")
    print("Make sure api/app/clients/odoo.py exists")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'sage_migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Run SAGE to Odoo migration."""
    
    print("=" * 70)
    print("SAGE to Odoo v18 Migration")
    print("=" * 70)
    print()
    
    # Step 1: Check environment variables
    print("Step 1: Checking configuration...")
    required_vars = [
        'SAGE_BASE_URL',
        'SAGE_API_KEY',
        'SAGE_API_SECRET',
        'ODOO_URL',
        'ODOO_DB',
        'ODOO_USERNAME',
        'ODOO_PASSWORD'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print()
        print("Please set these in your .env file:")
        for var in missing_vars:
            print(f"  {var}=your_value_here")
        return 1
    
    print("✓ All required environment variables set")
    print()
    
    # Step 2: Get migration parameters
    print("Step 2: Migration parameters...")
    years_of_data = int(input("How many years of data to migrate? [1]: ") or "1")
    print(f"✓ Will migrate {years_of_data} year(s) of data")
    print()
    
    # Step 3: Calculate pricing
    print("Step 3: Calculating migration cost...")
    pricing_engine = MigrationPricingEngine()
    
    # Estimate cost (you can update this with actual record counts if known)
    cost_estimate = pricing_engine.estimate_migration_cost(
        platform='sage',
        years_of_data=years_of_data,
        estimated_record_count=None  # Will use default estimates
    )
    
    print(f"Estimated cost: ${cost_estimate['total_cost']:.2f}")
    print(f"  Base price: ${cost_estimate['base_price']:.2f}")
    print(f"  Data volume charge: ${cost_estimate['volume_charge']:.2f}")
    print(f"  Platform multiplier: {cost_estimate['platform_multiplier']}x")
    print()
    
    proceed = input("Proceed with migration? (yes/no): ")
    if proceed.lower() not in ['yes', 'y']:
        print("Migration cancelled")
        return 0
    print()
    
    # Step 4: Initialize clients
    print("Step 4: Connecting to SAGE and Odoo...")
    try:
        sage_client = SAGEClient()
        odoo_client = OdooClient(
            url=os.getenv('ODOO_URL'),
            db=os.getenv('ODOO_DB'),
            username=os.getenv('ODOO_USERNAME'),
            password=os.getenv('ODOO_PASSWORD')
        )
        
        # Test connections
        if not sage_client.test_connection():
            print("❌ Failed to connect to SAGE")
            return 1
        
        if not odoo_client.authenticate():
            print("❌ Failed to connect to Odoo")
            return 1
        
        print("✓ Connected to SAGE and Odoo")
        print()
        
    except Exception as e:
        print(f"❌ Error connecting to APIs: {e}")
        return 1
    
    # Step 5: Initialize migration orchestrator
    print("Step 5: Initializing migration orchestrator...")
    orchestrator = MigrationOrchestrator(
        source_client=sage_client,
        target_client=odoo_client,
        platform_mapper=PlatformMapper('sage', 'odoo'),
        mapping_config_path='config/sage_to_odoo_mapping.json'
    )
    print("✓ Migration orchestrator ready")
    print()
    
    # Step 6: Run migration
    print("Step 6: Running migration...")
    print("This may take several minutes...")
    print()
    
    try:
        result = orchestrator.run_full_migration(
            years_of_data=years_of_data,
            validate=True,
            generate_report=True
        )
        
        print()
        print("=" * 70)
        print("Migration Complete!")
        print("=" * 70)
        print()
        print(f"Status: {result['status']}")
        print(f"Total records migrated: {result['total_records']}")
        print(f"Duration: {result['duration']}")
        print()
        print("Breakdown by entity:")
        for entity, count in result['entity_counts'].items():
            print(f"  {entity}: {count}")
        print()
        print(f"Report saved to: {result['report_file']}")
        print()
        
        if result['status'] == 'success':
            print("✓ Migration completed successfully!")
            return 0
        else:
            print("⚠ Migration completed with warnings")
            print(f"Check the report for details: {result['report_file']}")
            return 0
            
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        print()
        print(f"❌ Migration failed: {e}")
        print("Check the log file for details")
        return 1


if __name__ == "__main__":
    sys.exit(main())

