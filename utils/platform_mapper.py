"""
Platform Mapper - Universal mapping utility for ANY platform to Odoo migration.
Supports QuickBooks, SAGE, Wave, Expensify, doola, Dext, and more.
"""

import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class PlatformMapper:
    """Universal mapper for transforming any accounting platform data to Odoo."""
    
    def __init__(self, mapping_config_path: str):
        """
        Initialize platform mapper with mapping configuration.
        
        Args:
            mapping_config_path: Path to JSON mapping configuration file
        """
        self.mapping_config = self._load_mapping_config(mapping_config_path)
        self.entity_mapping_cache = {}  # QB/Source ID -> Odoo ID cache
        
    def _load_mapping_config(self, config_path: str) -> Dict:
        """Load mapping configuration from JSON file."""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def transform_entity(self, source_entity_type: str, source_data: Dict, 
                        odoo_client: Any = None) -> Dict:
        """
        Transform source platform entity to Odoo format.
        
        Args:
            source_entity_type: Source entity type (e.g., "Customer", "Invoice")
            source_data: Source platform data
            odoo_client: Optional Odoo client for lookups
            
        Returns:
            Transformed data ready for Odoo
        """
        # Get mapping for this entity type
        entity_config = self.mapping_config["entity_mappings"].get(source_entity_type)
        
        if not entity_config:
            raise ValueError(f"No mapping configured for entity type: {source_entity_type}")
        
        odoo_vals = {}
        
        # Transform fields based on mapping
        for source_field, odoo_field in entity_config["field_mappings"].items():
            source_value = self._get_nested_value(source_data, source_field)
            
            if source_value is not None:
                # Check if transformation needed
                transformation = self._get_field_transformation(source_field)
                
                if transformation:
                    odoo_value = self._apply_transformation(
                        source_value, 
                        transformation, 
                        source_data,
                        odoo_client
                    )
                else:
                    odoo_value = source_value
                
                odoo_vals[odoo_field] = odoo_value
        
        # Add computed fields
        computed = entity_config.get("computed_fields", {})
        odoo_vals.update(computed)
        
        return odoo_vals
    
    def _get_nested_value(self, data: Dict, field_path: str) -> Any:
        """
        Get value from nested dictionary using dot notation.
        
        Args:
            data: Source data dictionary
            field_path: Field path (e.g., "BillAddr.Line1")
            
        Returns:
            Value or None if not found
        """
        parts = field_path.split(".")
        value = data
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
            
            if value is None:
                return None
        
        return value
    
    def _get_field_transformation(self, field_path: str) -> Optional[Dict]:
        """Get transformation rule for a field if it exists."""
        transformations = self.mapping_config.get("field_transformations", {})
        
        # Check for exact match or pattern match
        for key, transformation in transformations.items():
            if key in field_path.lower() or field_path.endswith(key):
                return transformation
        
        return None
    
    def _apply_transformation(self, value: Any, transformation: Dict, 
                             source_data: Dict, odoo_client: Any) -> Any:
        """
        Apply transformation rule to a value.
        
        Args:
            value: Source value
            transformation: Transformation rule
            source_data: Complete source data for context
            odoo_client: Odoo client for lookups
            
        Returns:
            Transformed value
        """
        trans_type = transformation.get("type")
        
        if trans_type == "composite":
            # Combine multiple fields
            fields = transformation.get("fields", [])
            separator = transformation.get("separator", " ")
            parts = []
            for field in fields:
                val = self._get_nested_value(source_data, field)
                if val:
                    parts.append(val)
            return separator.join(parts)
        
        elif trans_type == "lookup":
            # Lookup in Odoo model
            if not odoo_client:
                return None
            
            target_model = transformation.get("target_model")
            search_field = transformation.get("search_field")
            
            # Search for record
            records = odoo_client.search_read(
                target_model,
                [(search_field, "=", value)],
                ["id"]
            )
            
            return records[0]["id"] if records else None
        
        elif trans_type == "mapping_lookup":
            # Lookup using entity mapping cache
            source_field = transformation.get("source_field")
            source_id = self._get_nested_value(source_data, source_field)
            
            if source_id:
                entity_key = f"{source_field.split('.')[0]}_{source_id}"
                return self.entity_mapping_cache.get(entity_key)
            
            return None
        
        elif trans_type == "date":
            # Convert date format
            if isinstance(value, str):
                try:
                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    return dt.date().isoformat()
                except:
                    return value
            return value
        
        elif trans_type == "boolean_inverse":
            # Invert boolean (e.g., Active -> deprecated)
            return not value
        
        return value
    
    def get_migration_sequence(self) -> List[str]:
        """Get the correct migration sequence."""
        return self.mapping_config.get("migration_sequence", [])
    
    def get_odoo_model(self, source_entity_type: str) -> str:
        """Get Odoo model for source entity type."""
        entity_config = self.mapping_config["entity_mappings"].get(source_entity_type)
        if entity_config:
            return entity_config["odoo_model"]
        return None


class QuickBooksToOdooMapper(PlatformMapper):
    """Specialized mapper for QuickBooks to Odoo migration."""
    
    def __init__(self):
        """Initialize QuickBooks mapper with default config."""
        config_path = Path(__file__).parent.parent / "config" / "quickbooks_to_odoo_mapping.json"
        super().__init__(str(config_path))
    
    def transform_customer(self, qb_customer: Dict, odoo_client: Any = None) -> Dict:
        """Transform QuickBooks Customer to Odoo res.partner."""
        base_vals = self.transform_entity("Customer", qb_customer, odoo_client)
        
        # Additional QuickBooks-specific transformations
        if qb_customer.get("CompanyName"):
            base_vals["company_type"] = "company"
        else:
            base_vals["company_type"] = "person"
        
        # Handle shipping address as child contact if different
        ship_addr = qb_customer.get("ShipAddr")
        bill_addr = qb_customer.get("BillAddr")
        
        if ship_addr and ship_addr != bill_addr:
            # Note: Shipping address will be handled as delivery contact
            base_vals["child_ids"] = [(0, 0, {
                "name": f"{qb_customer.get('DisplayName')} - Shipping",
                "type": "delivery",
                "street": ship_addr.get("Line1", ""),
                "city": ship_addr.get("City", ""),
                "zip": ship_addr.get("PostalCode", "")
            })]
        
        return base_vals
    
    def transform_vendor(self, qb_vendor: Dict, odoo_client: Any = None) -> Dict:
        """Transform QuickBooks Vendor to Odoo res.partner."""
        base_vals = self.transform_entity("Vendor", qb_vendor, odoo_client)
        
        # Lookup payment term if available
        if qb_vendor.get("TermRef") and odoo_client:
            term_name = qb_vendor["TermRef"].get("name")
            terms = odoo_client.search_read(
                "account.payment.term",
                [("name", "ilike", term_name)],
                ["id"]
            )
            if terms:
                base_vals["property_supplier_payment_term_id"] = terms[0]["id"]
        
        return base_vals
    
    def transform_account(self, qb_account: Dict, odoo_client: Any = None) -> Dict:
        """Transform QuickBooks Account to Odoo account.account."""
        base_vals = self.transform_entity("Account", qb_account, odoo_client)
        
        # Map account type
        qb_account_type = qb_account.get("AccountType")
        qb_account_subtype = qb_account.get("AccountSubType")
        
        # Get account type mapping
        entity_config = self.mapping_config["entity_mappings"]["Account"]
        type_mapping = entity_config.get("type_mapping", {})
        
        odoo_account_type = type_mapping.get(qb_account_type, "expenses")
        
        # Lookup Odoo account type ID
        if odoo_client:
            account_types = odoo_client.search_read(
                "account.account.type",
                [("internal_group", "=", odoo_account_type)],
                ["id"]
            )
            if account_types:
                base_vals["user_type_id"] = account_types[0]["id"]
        
        # Handle deprecated (opposite of Active)
        if "Active" in qb_account:
            base_vals["deprecated"] = not qb_account["Active"]
        
        return base_vals
    
    def transform_product(self, qb_item: Dict, odoo_client: Any = None) -> Dict:
        """Transform QuickBooks Item to Odoo product.product."""
        base_vals = self.transform_entity("Item", qb_item, odoo_client)
        
        # Map item type
        qb_type = qb_item.get("Type")
        entity_config = self.mapping_config["entity_mappings"]["Item"]
        type_mapping = entity_config.get("type_mapping", {})
        
        odoo_type = type_mapping.get(qb_type, "consu")
        base_vals["type"] = odoo_type
        
        # Track inventory if QBO tracks quantity
        if qb_item.get("TrackQtyOnHand"):
            base_vals["type"] = "product"
        
        return base_vals
    
    def transform_invoice(self, qb_invoice: Dict, odoo_client: Any = None) -> Dict:
        """Transform QuickBooks Invoice to Odoo account.move."""
        base_vals = self.transform_entity("Invoice", qb_invoice, odoo_client)
        
        # Transform invoice lines
        qb_lines = qb_invoice.get("Line", [])
        odoo_lines = []
        
        for qb_line in qb_lines:
            # Skip subtotal/discount lines
            if qb_line.get("DetailType") not in ["SalesItemLineDetail"]:
                continue
            
            detail = qb_line.get("SalesItemLineDetail", {})
            
            line_vals = {
                "name": qb_line.get("Description") or detail.get("ItemRef", {}).get("name", ""),
                "quantity": detail.get("Qty", 1),
                "price_unit": detail.get("UnitPrice", 0),
            }
            
            # Lookup product if available
            item_id = detail.get("ItemRef", {}).get("value")
            if item_id and f"Item_{item_id}" in self.entity_mapping_cache:
                line_vals["product_id"] = self.entity_mapping_cache[f"Item_{item_id}"]
            
            # Lookup account
            account_id = detail.get("IncomeAccountRef", {}).get("value")
            if account_id and f"Account_{account_id}" in self.entity_mapping_cache:
                line_vals["account_id"] = self.entity_mapping_cache[f"Account_{account_id}"]
            
            odoo_lines.append((0, 0, line_vals))
        
        base_vals["invoice_line_ids"] = odoo_lines
        
        # Lookup customer
        customer_id = qb_invoice.get("CustomerRef", {}).get("value")
        if customer_id and f"Customer_{customer_id}" in self.entity_mapping_cache:
            base_vals["partner_id"] = self.entity_mapping_cache[f"Customer_{customer_id}"]
        
        return base_vals
    
    def transform_bill(self, qb_bill: Dict, odoo_client: Any = None) -> Dict:
        """Transform QuickBooks Bill to Odoo account.move."""
        base_vals = self.transform_entity("Bill", qb_bill, odoo_client)
        
        # Transform bill lines
        qb_lines = qb_bill.get("Line", [])
        odoo_lines = []
        
        for qb_line in qb_lines:
            if qb_line.get("DetailType") not in ["AccountBasedExpenseLineDetail", "ItemBasedExpenseLineDetail"]:
                continue
            
            detail = qb_line.get("AccountBasedExpenseLineDetail") or qb_line.get("ItemBasedExpenseLineDetail", {})
            
            line_vals = {
                "name": qb_line.get("Description", ""),
                "quantity": detail.get("Qty", 1),
                "price_unit": detail.get("UnitPrice", qb_line.get("Amount", 0)),
            }
            
            # Lookup account
            account_id = detail.get("AccountRef", {}).get("value") or detail.get("ExpenseAccountRef", {}).get("value")
            if account_id and f"Account_{account_id}" in self.entity_mapping_cache:
                line_vals["account_id"] = self.entity_mapping_cache[f"Account_{account_id}"]
            
            odoo_lines.append((0, 0, line_vals))
        
        base_vals["invoice_line_ids"] = odoo_lines
        
        # Lookup vendor
        vendor_id = qb_bill.get("VendorRef", {}).get("value")
        if vendor_id and f"Vendor_{vendor_id}" in self.entity_mapping_cache:
            base_vals["partner_id"] = self.entity_mapping_cache[f"Vendor_{vendor_id}"]
        
        return base_vals
    
    def transform_payment(self, qb_payment: Dict, payment_type: str = "inbound", 
                         odoo_client: Any = None) -> Dict:
        """Transform QuickBooks Payment to Odoo account.payment."""
        entity_type = "Payment" if payment_type == "inbound" else "BillPayment"
        base_vals = self.transform_entity(entity_type, qb_payment, odoo_client)
        
        # Lookup partner
        if payment_type == "inbound":
            partner_id = qb_payment.get("CustomerRef", {}).get("value")
            if partner_id and f"Customer_{partner_id}" in self.entity_mapping_cache:
                base_vals["partner_id"] = self.entity_mapping_cache[f"Customer_{partner_id}"]
        else:
            partner_id = qb_payment.get("VendorRef", {}).get("value")
            if partner_id and f"Vendor_{partner_id}" in self.entity_mapping_cache:
                base_vals["partner_id"] = self.entity_mapping_cache[f"Vendor_{partner_id}"]
        
        # Lookup payment method
        payment_method = qb_payment.get("PaymentMethodRef", {}).get("name", "")
        if odoo_client and payment_method:
            methods = odoo_client.search_read(
                "account.payment.method",
                [("name", "ilike", payment_method)],
                ["id"]
            )
            if methods:
                base_vals["payment_method_id"] = methods[0]["id"]
        
        return base_vals
    
    def transform_journal_entry(self, qb_je: Dict, odoo_client: Any = None) -> Dict:
        """Transform QuickBooks Journal Entry to Odoo account.move."""
        base_vals = self.transform_entity("JournalEntry", qb_je, odoo_client)
        
        # Transform journal entry lines
        qb_lines = qb_je.get("Line", [])
        odoo_lines = []
        
        for qb_line in qb_lines:
            detail = qb_line.get("JournalEntryLineDetail", {})
            
            # Determine debit/credit
            posting_type = detail.get("PostingType")  # Debit or Credit
            amount = qb_line.get("Amount", 0)
            
            line_vals = {
                "name": qb_line.get("Description", "/"),
                "debit": amount if posting_type == "Debit" else 0,
                "credit": amount if posting_type == "Credit" else 0,
            }
            
            # Lookup account
            account_id = detail.get("AccountRef", {}).get("value")
            if account_id and f"Account_{account_id}" in self.entity_mapping_cache:
                line_vals["account_id"] = self.entity_mapping_cache[f"Account_{account_id}"]
            
            # Lookup analytic account (Class in QB)
            class_id = detail.get("ClassRef", {}).get("value")
            if class_id and f"Class_{class_id}" in self.entity_mapping_cache:
                line_vals["analytic_account_id"] = self.entity_mapping_cache[f"Class_{class_id}"]
            
            odoo_lines.append((0, 0, line_vals))
        
        base_vals["line_ids"] = odoo_lines
        
        return base_vals
    
    def get_migration_statistics(self) -> Dict:
        """Get migration statistics."""
        return {
            "entities_mapped": len(self.entity_mapping_cache),
            "errors": len(self.errors) if hasattr(self, 'errors') else 0,
            "mapping_config_version": self.mapping_config.get("metadata", {}).get("version"),
            "source_platform": self.mapping_config.get("metadata", {}).get("source_platform"),
            "target_platform": self.mapping_config.get("metadata", {}).get("target_platform")
        }


# Factory functions for different platforms
def get_quickbooks_mapper() -> QuickBooksToOdooMapper:
    """Get QuickBooks to Odoo mapper."""
    return QuickBooksToOdooMapper()


def get_sage_mapper() -> PlatformMapper:
    """Get SAGE to Odoo mapper."""
    config_path = Path(__file__).parent.parent / "config" / "sage_to_odoo_mapping.json"
    return PlatformMapper(str(config_path))


def get_wave_mapper() -> PlatformMapper:
    """Get Wave to Odoo mapper."""
    config_path = Path(__file__).parent.parent / "config" / "wave_to_odoo_mapping.json"
    return PlatformMapper(str(config_path))


def get_mapper_for_platform(platform_name: str) -> PlatformMapper:
    """
    Get appropriate mapper for platform.
    
    Args:
        platform_name: Platform name (e.g., "QuickBooks", "SAGE", "Wave")
        
    Returns:
        PlatformMapper instance
    """
    platform_lower = platform_name.lower()
    
    if "quickbooks" in platform_lower or "qbo" in platform_lower:
        return get_quickbooks_mapper()
    elif "sage" in platform_lower:
        return get_sage_mapper()
    elif "wave" in platform_lower:
        return get_wave_mapper()
    else:
        raise ValueError(f"No mapper configured for platform: {platform_name}")

