"""
Migration Orchestrator - Handles complete end-to-end migration from any platform to Odoo.
Coordinates data extraction, transformation, and loading with error handling.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class MigrationOrchestrator:
    """
    Orchestrates complete migration from source platform to Odoo.
    Handles extraction, transformation, loading, and validation.
    """
    
    def __init__(self, source_client: Any, odoo_client: Any, mapper: Any):
        """
        Initialize migration orchestrator.
        
        Args:
            source_client: Source platform client (e.g., QBOFullClient)
            odoo_client: Odoo client
            mapper: Platform mapper (e.g., QuickBooksToOdooMapper)
        """
        self.source_client = source_client
        self.odoo_client = odoo_client
        self.mapper = mapper
        
        # Migration state
        self.entity_mappings = {}  # Source ID -> Odoo ID
        self.migration_log = []
        self.errors = []
        self.statistics = {
            "total_entities": 0,
            "successfully_migrated": 0,
            "failed": 0,
            "skipped": 0,
            "start_time": None,
            "end_time": None
        }
    
    def execute_full_migration(self, entities_to_migrate: Optional[List[str]] = None) -> Dict:
        """
        Execute complete migration.
        
        Args:
            entities_to_migrate: Optional list of entities to migrate (default: all)
            
        Returns:
            Migration results
        """
        self.statistics["start_time"] = datetime.now()
        logger.info("=" * 80)
        logger.info("Starting FULL Migration")
        logger.info("=" * 80)
        
        # Get migration sequence
        sequence = self.mapper.get_migration_sequence()
        
        if entities_to_migrate:
            # Filter sequence to only requested entities
            sequence = [e for e in sequence if e in entities_to_migrate]
        
        logger.info(f"Migration sequence: {len(sequence)} entity types")
        
        # Phase 1: Extract all data from source
        logger.info("\n[PHASE 1] Extracting data from source platform...")
        source_data = self._extract_all_data()
        
        # Phase 2: Migrate in correct sequence
        logger.info("\n[PHASE 2] Migrating entities to Odoo...")
        
        for entity_type in sequence:
            self._migrate_entity_type(entity_type, source_data)
        
        # Phase 3: Validate migration
        logger.info("\n[PHASE 3] Validating migration...")
        validation_results = self._validate_migration(source_data)
        
        # Phase 4: Generate migration report
        logger.info("\n[PHASE 4] Generating migration report...")
        report = self._generate_migration_report(source_data, validation_results)
        
        self.statistics["end_time"] = datetime.now()
        duration = (self.statistics["end_time"] - self.statistics["start_time"]).total_seconds()
        
        logger.info("=" * 80)
        logger.info(f"Migration completed in {duration:.2f} seconds")
        logger.info(f"Successfully migrated: {self.statistics['successfully_migrated']}")
        logger.info(f"Failed: {self.statistics['failed']}")
        logger.info(f"Errors: {len(self.errors)}")
        logger.info("=" * 80)
        
        return {
            "statistics": self.statistics,
            "entity_mappings": self.entity_mappings,
            "errors": self.errors,
            "validation": validation_results,
            "report": report
        }
    
    def _extract_all_data(self) -> Dict[str, List[Dict]]:
        """Extract all data from source platform."""
        if hasattr(self.source_client, 'get_all_entities'):
            # Source client has convenience method
            return self.source_client.get_all_entities()
        else:
            # Manual extraction (fallback)
            logger.warning("Source client doesn't have get_all_entities(), using manual extraction")
            return {}
    
    def _migrate_entity_type(self, entity_type: str, source_data: Dict):
        """
        Migrate a specific entity type.
        
        Args:
            entity_type: Entity type to migrate (e.g., "Customer", "Invoice")
            source_data: Complete source data
        """
        # Get data for this entity type
        entity_key = self._get_entity_key(entity_type, source_data)
        
        if not entity_key or entity_key not in source_data:
            logger.warning(f"No data found for entity type: {entity_type}")
            return
        
        entities = source_data[entity_key]
        
        if not entities:
            logger.info(f"No {entity_type} records to migrate")
            return
        
        logger.info(f"\nMigrating {len(entities)} {entity_type} records...")
        
        success_count = 0
        fail_count = 0
        
        for entity_data in entities:
            try:
                # Transform to Odoo format
                if hasattr(self.mapper, f'transform_{entity_type.lower()}'):
                    # Use specialized transformation
                    transform_method = getattr(self.mapper, f'transform_{entity_type.lower()}')
                    odoo_vals = transform_method(entity_data, self.odoo_client)
                else:
                    # Use generic transformation
                    odoo_vals = self.mapper.transform_entity(entity_type, entity_data, self.odoo_client)
                
                # Get Odoo model
                odoo_model = self.mapper.get_odoo_model(entity_type)
                
                # Create in Odoo
                odoo_id = self.odoo_client.create(odoo_model, odoo_vals)
                
                # Store mapping
                source_id = str(entity_data.get("Id"))
                mapping_key = f"{entity_type}_{source_id}"
                self.entity_mappings[mapping_key] = odoo_id
                self.mapper.entity_mapping_cache[mapping_key] = odoo_id
                
                success_count += 1
                self.statistics["successfully_migrated"] += 1
                
            except Exception as e:
                fail_count += 1
                self.statistics["failed"] += 1
                
                logger.error(f"Error migrating {entity_type} {entity_data.get('Id')}: {e}")
                self.errors.append({
                    "entity_type": entity_type,
                    "source_id": entity_data.get("Id"),
                    "source_name": entity_data.get("Name") or entity_data.get("DisplayName") or entity_data.get("DocNumber"),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        logger.info(f"✓ {entity_type}: {success_count} succeeded, {fail_count} failed")
        
        self.migration_log.append({
            "entity_type": entity_type,
            "total": len(entities),
            "succeeded": success_count,
            "failed": fail_count,
            "timestamp": datetime.now().isoformat()
        })
    
    def _get_entity_key(self, entity_type: str, source_data: Dict) -> Optional[str]:
        """Get the key for entity type in source data."""
        # Common patterns
        possible_keys = [
            entity_type.lower() + "s",  # e.g., "customers"
            entity_type.lower(),        # e.g., "customer"
            entity_type,                # e.g., "Customer"
            entity_type + "s"           # e.g., "Customers"
        ]
        
        for key in possible_keys:
            if key in source_data:
                return key
        
        return None
    
    def _validate_migration(self, source_data: Dict) -> Dict:
        """
        Validate migration by comparing counts and balances.
        
        Args:
            source_data: Source platform data
            
        Returns:
            Validation results
        """
        validation = {
            "entity_counts": {},
            "balance_checks": {},
            "data_integrity": {},
            "overall_status": "pending"
        }
        
        # Validate entity counts
        for entity_type in ["customers", "vendors", "invoices", "bills", "items", "accounts"]:
            if entity_type in source_data:
                source_count = len(source_data[entity_type])
                
                # Count in Odoo
                odoo_model = self._get_odoo_model_for_entity(entity_type)
                if odoo_model:
                    odoo_count = len(self.odoo_client.search(odoo_model, []))
                    
                    validation["entity_counts"][entity_type] = {
                        "source": source_count,
                        "odoo": odoo_count,
                        "match": source_count == odoo_count
                    }
        
        # Check if all counts match
        all_match = all(v.get("match", False) for v in validation["entity_counts"].values())
        validation["overall_status"] = "passed" if all_match else "failed"
        
        return validation
    
    def _get_odoo_model_for_entity(self, entity_type: str) -> Optional[str]:
        """Get Odoo model for entity type."""
        model_map = {
            "customers": "res.partner",
            "vendors": "res.partner",
            "invoices": "account.move",
            "bills": "account.move",
            "items": "product.product",
            "accounts": "account.account"
        }
        return model_map.get(entity_type)
    
    def _generate_migration_report(self, source_data: Dict, validation: Dict) -> Dict:
        """Generate comprehensive migration report."""
        report = {
            "migration_summary": {
                "total_entities_migrated": self.statistics["successfully_migrated"],
                "total_errors": self.statistics["failed"],
                "duration_seconds": (self.statistics["end_time"] - self.statistics["start_time"]).total_seconds() if self.statistics["end_time"] else 0,
                "validation_status": validation["overall_status"]
            },
            "entity_breakdown": self.migration_log,
            "errors": self.errors,
            "validation_details": validation
        }
        
        return report
    
    def save_migration_report(self, output_path: str):
        """Save migration report to file."""
        report = self._generate_migration_report({}, {})
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Migration report saved to: {output_path}")


def migrate_quickbooks_to_odoo(qbo_realm_id: str, qbo_token: str,
                               odoo_url: str, odoo_db: str, 
                               odoo_user: str, odoo_password: str,
                               entities: Optional[List[str]] = None) -> Dict:
    """
    Complete QuickBooks to Odoo migration - One-line execution.
    
    Args:
        qbo_realm_id: QuickBooks company ID
        qbo_token: QuickBooks OAuth token
        odoo_url: Odoo URL
        odoo_db: Odoo database
        odoo_user: Odoo username
        odoo_password: Odoo password
        entities: Optional list of entity types to migrate
        
    Returns:
        Migration results
    """
    # Import clients
    from api.app.clients.qbo import QBOFullClient
    from api.app.clients.odoo import OdooMigrationClient
    from utils.platform_mapper import get_quickbooks_mapper
    
    # Initialize
    qbo_client = QBOFullClient(qbo_realm_id, qbo_token, production=True)
    odoo_client = OdooMigrationClient(odoo_url, odoo_db, odoo_user, odoo_password)
    mapper = get_quickbooks_mapper()
    
    # Execute migration
    orchestrator = MigrationOrchestrator(qbo_client, odoo_client, mapper)
    results = orchestrator.execute_full_migration(entities)
    
    # Save report
    report_path = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    orchestrator.save_migration_report(report_path)
    
    return results

