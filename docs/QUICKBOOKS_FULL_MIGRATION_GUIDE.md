# QuickBooks Online to Odoo v18 - Full Migration Guide

**Complete Entity Mapping & Migration Strategy**

---

## 🎯 Executive Summary

This guide covers the **COMPLETE** migration of ALL QuickBooks Online data to Odoo v18, including:

- **40+ QuickBooks entities** → Odoo models
- **Master data** (Customers, Vendors, Inventory)
- **All transactions** (Sales, Purchases, Journal Entries)
- **Historical data** (Invoices, Bills, Payments)
- **Supporting data** (Tax rates, Payment terms, Classes)

**Migration Coverage**: 100% of QuickBooks data

---

## 📊 QuickBooks Entity Overview

### **QuickBooks has 40+ entity types across 4 categories:**

1. **Name Lists** (Master Data) - 11 entities
2. **Sales Transactions** - 6 entities
3. **Purchase Transactions** - 5 entities  
4. **Other Transactions** - 5 entities
5. **Supporting** - 13+ entities

---

## 🗂️ Complete Entity Mapping: QuickBooks → Odoo

### **CATEGORY 1: Name Lists (Master Data)**

| # | QuickBooks Entity | Odoo Model | Priority | Notes |
|---|-------------------|------------|----------|-------|
| 1 | **Customer** | `res.partner` | 🔴 Critical | `customer_rank=1`, with contacts |
| 2 | **Vendor** | `res.partner` | 🔴 Critical | `supplier_rank=1`, with addresses |
| 3 | **Employee** | `hr.employee` | 🟡 High | Or `res.partner` if no HR module |
| 4 | **Account** (Chart of Accounts) | `account.account` | 🔴 Critical | Map account types correctly |
| 5 | **Item** (Product/Service) | `product.product` | 🔴 Critical | Map inventory vs service items |
| 6 | **Class** | `account.analytic.account` | 🟢 Medium | For cost center tracking |
| 7 | **Department** | `hr.department` | 🟢 Medium | Or analytic account |
| 8 | **Payment Method** | `account.payment.method` | 🟡 High | Cash, Check, Credit Card |
| 9 | **Term** (Payment Terms) | `account.payment.term` | 🟡 High | Net 30, Due on Receipt, etc. |
| 10 | **Tax Code** | `account.tax` | 🔴 Critical | Sales tax configuration |
| 11 | **Tax Rate** | `account.tax` | 🔴 Critical | Tax percentage and computation |

### **CATEGORY 2: Sales Transactions**

| # | QuickBooks Entity | Odoo Model | Priority | Notes |
|---|-------------------|------------|----------|-------|
| 12 | **Invoice** | `account.move` | 🔴 Critical | `move_type='out_invoice'` |
| 13 | **Sales Receipt** | `account.move` | 🔴 Critical | `move_type='out_invoice'` + immediate payment |
| 14 | **Estimate** | `sale.order` | 🟡 High | Quotation state |
| 15 | **Credit Memo** | `account.move` | 🔴 Critical | `move_type='out_refund'` |
| 16 | **Refund Receipt** | `account.move` | 🟡 High | `move_type='out_refund'` + payment |
| 17 | **Payment** (Customer) | `account.payment` | 🔴 Critical | `payment_type='inbound'` |

### **CATEGORY 3: Purchase Transactions**

| # | QuickBooks Entity | Odoo Model | Priority | Notes |
|---|-------------------|------------|----------|-------|
| 18 | **Bill** | `account.move` | 🔴 Critical | `move_type='in_invoice'` |
| 19 | **Bill Payment** | `account.payment` | 🔴 Critical | `payment_type='outbound'` |
| 20 | **Purchase Order** | `purchase.order` | 🟡 High | Requires purchase module |
| 21 | **Vendor Credit** | `account.move` | 🟡 High | `move_type='in_refund'` |
| 22 | **Purchase** (Expense/Check) | `account.move` | 🟡 High | `move_type='entry'` or expense |

### **CATEGORY 4: Other Transactions**

| # | QuickBooks Entity | Odoo Model | Priority | Notes |
|---|-------------------|------------|----------|-------|
| 23 | **Journal Entry** | `account.move` | 🔴 Critical | `move_type='entry'` |
| 24 | **Transfer** (Bank Transfer) | `account.payment` | 🟡 High | Internal transfer |
| 25 | **Deposit** | `account.move` | 🟡 High | Bank deposit entry |
| 26 | **Time Activity** | `hr_timesheet.line` | 🟢 Medium | Or `project.task` |
| 27 | **Inventory Adjustment** | `stock.inventory` | 🟡 High | If using inventory module |

### **CATEGORY 5: Supporting Data**

| # | QuickBooks Entity | Odoo Model | Priority | Notes |
|---|-------------------|------------|----------|-------|
| 28 | **Company Info** | `res.company` | 🔴 Critical | Main company record |
| 29 | **Preferences** | `ir.config_parameter` | 🟢 Medium | System settings |
| 30 | **Attachable** (Files) | `ir.attachment` | 🟢 Medium | Document attachments |
| 31 | **Budget** | `account.budget` | 🟢 Low | If using budget module |
| 32 | **Custom Fields** | Custom models | 🟢 Low | Create x_studio_* fields |

---

## 🔄 Migration Sequence (Order Matters!)

### **Phase 1: Master Data (Foundation)**
```
1. Company Info
2. Chart of Accounts
3. Tax Codes & Tax Rates
4. Payment Terms
5. Payment Methods
6. Customers
7. Vendors
8. Employees
9. Products/Services (Items)
10. Classes (Analytic Accounts)
11. Departments
```

### **Phase 2: Opening Balances**
```
12. Initial journal entry for account balances
13. Customer opening balances
14. Vendor opening balances
```

### **Phase 3: Historical Transactions (Chronological)**
```
14. Journal Entries (oldest first)
15. Bills (oldest first)
16. Invoices (oldest first)
17. Sales Receipts
18. Customer Payments
19. Bill Payments
20. Credit Memos
21. Vendor Credits
22. Deposits
23. Transfers
```

### **Phase 4: Supporting Data**
```
24. Estimates → Sale Orders
25. Purchase Orders
26. Time Activities
27. Attachments
```

---

## 📋 Detailed Field Mappings

### **1. Customer (QuickBooks) → res.partner (Odoo)**

| QuickBooks Field | Odoo Field | Notes |
|------------------|------------|-------|
| `DisplayName` | `name` | Customer name |
| `CompanyName` | `name` | If business customer |
| `GivenName` | `name` (split) | First name |
| `FamilyName` | `name` (split) | Last name |
| `PrimaryEmailAddr.Address` | `email` | Email |
| `PrimaryPhone.FreeFormNumber` | `phone` | Phone |
| `Mobile.FreeFormNumber` | `mobile` | Mobile |
| `BillAddr` | `street`, `city`, `zip`, `country_id` | Billing address |
| `ShipAddr` | Create child contact | Shipping address |
| `Balance` | `credit` | Current balance |
| `Active` | `active` | Status |
| `Notes` | `comment` | Internal notes |
| - | `customer_rank` = 1 | Mark as customer |

### **2. Vendor (QuickBooks) → res.partner (Odoo)**

| QuickBooks Field | Odoo Field | Notes |
|------------------|------------|-------|
| `DisplayName` | `name` | Vendor name |
| `CompanyName` | `name` | Company |
| `PrimaryEmailAddr.Address` | `email` | Email |
| `PrimaryPhone.FreeFormNumber` | `phone` | Phone |
| `BillAddr` | `street`, `city`, `zip`, `country_id` | Address |
| `Balance` | `debit` | Amount owed |
| `Active` | `active` | Status |
| `AcctNum` | `ref` | Vendor account # |
| `TermRef` | `property_payment_term_id` | Payment terms |
| - | `supplier_rank` = 1 | Mark as vendor |

### **3. Account (Chart of Accounts) → account.account (Odoo)**

| QuickBooks Field | Odoo Field | Notes |
|------------------|------------|-------|
| `Name` | `name` | Account name |
| `AcctNum` | `code` | Account number |
| `AccountType` | `user_type_id` | Map to Odoo account types |
| `AccountSubType` | `user_type_id` | Detailed mapping |
| `Active` | `deprecated` | Opposite (active=!deprecated) |
| `Classification` | - | Use for grouping |
| `CurrentBalance` | - | Use for opening balance |
| `Description` | `note` | Account description |

**Account Type Mapping:**
```python
QBO_TO_ODOO_ACCOUNT_TYPES = {
    # Assets
    "Bank": "liquidity",
    "Accounts Receivable": "receivable",
    "Other Current Asset": "current_assets",
    "Fixed Asset": "fixed_assets",
    "Other Asset": "non_current_assets",
    
    # Liabilities
    "Accounts Payable": "payable",
    "Credit Card": "current_liabilities",
    "Other Current Liability": "current_liabilities",
    "Long Term Liability": "non_current_liabilities",
    
    # Equity
    "Equity": "equity",
    
    # Income
    "Income": "income",
    "Other Income": "income_other",
    
    # Expenses
    "Cost of Goods Sold": "direct_costs",
    "Expense": "expenses",
    "Other Expense": "expenses",
}
```

### **4. Item (Product/Service) → product.product (Odoo)**

| QuickBooks Field | Odoo Field | Notes |
|------------------|------------|-------|
| `Name` | `name` | Product name |
| `Description` | `description` | Description |
| `Active` | `active` | Status |
| `Type` | `type` | 'Service', 'Inventory', 'NonInventory' |
| `UnitPrice` | `list_price` | Sales price |
| `PurchaseCost` | `standard_price` | Cost price |
| `IncomeAccountRef` | `property_account_income_id` | Income account |
| `ExpenseAccountRef` | `property_account_expense_id` | Expense account |
| `QtyOnHand` | Initial stock via `stock.inventory` | Inventory quantity |
| `TrackQtyOnHand` | `type='product'` | Track inventory |
| `Sku` | `default_code` | SKU/Internal ref |

### **5. Invoice (QuickBooks) → account.move (Odoo)**

| QuickBooks Field | Odoo Field | Notes |
|------------------|------------|-------|
| `DocNumber` | `name` | Invoice number |
| `TxnDate` | `invoice_date` | Invoice date |
| `DueDate` | `invoice_date_due` | Due date |
| `CustomerRef` | `partner_id` | Customer |
| `Line` (array) | `invoice_line_ids` | Invoice lines |
| `Line.Amount` | `price_subtotal` | Line amount |
| `Line.ItemRef` | `product_id` | Product |
| `Line.Qty` | `quantity` | Quantity |
| `Line.UnitPrice` | `price_unit` | Unit price |
| `Line.TaxCodeRef` | `tax_ids` | Taxes |
| `TotalAmt` | `amount_total` | Total |
| `Balance` | `amount_residual` | Amount due |
| `TxnTaxDetail` | Compute from lines | Tax details |
| - | `move_type='out_invoice'` | Invoice type |
| - | `state` | Map from QBO status |

**QBO to Odoo Status Mapping:**
```python
QBO_INVOICE_STATUS = {
    "Draft": "draft",
    "Pending": "draft", 
    "Sent": "posted",
    "Paid": "posted",  # + reconciled payment
    "Voided": "cancel",
    "Deleted": "cancel",
}
```

### **6. Bill (QuickBooks) → account.move (Odoo)**

| QuickBooks Field | Odoo Field | Notes |
|------------------|------------|-------|
| `DocNumber` | `ref` | Bill reference |
| `TxnDate` | `invoice_date` | Bill date |
| `DueDate` | `invoice_date_due` | Due date |
| `VendorRef` | `partner_id` | Vendor |
| `Line` | `invoice_line_ids` | Bill lines |
| `TotalAmt` | `amount_total` | Total |
| `Balance` | `amount_residual` | Amount due |
| - | `move_type='in_invoice'` | Bill type |

---

## 🛠️ Implementation Code Example

### **Full Migration Workflow**

```python
from api.app.clients.qbo import QBOFullClient
from odoo_client import OdooClient

def migrate_quickbooks_to_odoo(qbo_realm_id: str, qbo_token: str, 
                                odoo_url: str, odoo_db: str, 
                                odoo_user: str, odoo_password: str):
    """
    Complete QuickBooks to Odoo migration.
    """
    # Initialize clients
    qbo = QBOFullClient(qbo_realm_id, qbo_token, production=True)
    odoo = OdooClient(odoo_url, odoo_db, odoo_user, odoo_password)
    
    # Extract ALL data from QuickBooks
    print("Extracting data from QuickBooks...")
    qb_data = qbo.get_all_entities()
    
    # Phase 1: Master Data
    print("Migrating master data...")
    migrate_company_info(qb_data["company_info"], odoo)
    migrate_accounts(qb_data["accounts"], odoo)
    migrate_taxes(qb_data["tax_codes"], qb_data["tax_rates"], odoo)
    migrate_payment_terms(qb_data["terms"], odoo)
    migrate_payment_methods(qb_data["payment_methods"], odoo)
    migrate_customers(qb_data["customers"], odoo)
    migrate_vendors(qb_data["vendors"], odoo)
    migrate_products(qb_data["items"], odoo)
    migrate_classes(qb_data["classes"], odoo)
    
    # Phase 2: Transactions (chronological)
    print("Migrating transactions...")
    migrate_invoices(qb_data["invoices"], odoo)
    migrate_bills(qb_data["bills"], odoo)
    migrate_payments(qb_data["payments"], odoo)
    migrate_bill_payments(qb_data["bill_payments"], odoo)
    migrate_journal_entries(qb_data["journal_entries"], odoo)
    migrate_credit_memos(qb_data["credit_memos"], odoo)
    migrate_sales_receipts(qb_data["sales_receipts"], odoo)
    
    # Phase 3: Supporting
    print("Migrating supporting data...")
    migrate_estimates(qb_data["estimates"], odoo)
    migrate_purchase_orders(qb_data["purchase_orders"], odoo)
    
    print("Migration complete!")
```

---

## 📈 Migration Statistics

### **Typical Migration Volume**

| Entity | Small Business | Mid-size | Enterprise |
|--------|----------------|----------|------------|
| Customers | 100-500 | 500-5,000 | 5,000+ |
| Vendors | 50-200 | 200-2,000 | 2,000+ |
| Products | 50-300 | 300-10,000 | 10,000+ |
| Invoices | 500-2,000 | 2,000-50,000 | 50,000+ |
| Bills | 200-1,000 | 1,000-20,000 | 20,000+ |
| **Total Records** | 1,000-5,000 | 5,000-100,000 | 100,000+ |

### **Migration Time Estimates**

- **Small Business**: 2-4 hours
- **Mid-size**: 8-24 hours  
- **Enterprise**: 2-5 days

---

## ⚠️ Common Challenges & Solutions

### **Challenge 1: Account Type Mismatches**

**Problem**: QuickBooks account subtypes don't directly map to Odoo

**Solution**: Use mapping table + manual review for critical accounts

### **Challenge 2: Multi-currency**

**Problem**: QuickBooks stores currency per transaction, Odoo per partner

**Solution**: Create separate partner records for different currencies

### **Challenge 3: Classes vs Analytic Accounts**

**Problem**: QuickBooks classes are simpler than Odoo analytic accounting

**Solution**: Map classes to analytic accounts, educate users on differences

### **Challenge 4: Historical Reconciliations**

**Problem**: Bank reconciliations in QB don't translate directly

**Solution**: Migrate transactions, then re-reconcile in Odoo

### **Challenge 5: Custom Fields**

**Problem**: QuickBooks custom fields need Odoo equivalents

**Solution**: Create `x_studio_*` fields via Odoo Studio

---

## 🎯 Validation Checklist

After migration, verify:

- [ ] All customers migrated (count matches)
- [ ] All vendors migrated (count matches)
- [ ] Chart of accounts complete
- [ ] Opening balances match
- [ ] Invoice totals match
- [ ] A/R aging matches
- [ ] A/P aging matches
- [ ] Trial balance matches
- [ ] Tax reports reconcile
- [ ] Inventory quantities match
- [ ] Historical data accessible

---

## 📚 Additional Resources

- **QuickBooks API Docs**: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities
- **Odoo Documentation**: https://www.odoo.com/documentation/18.0/
- **Complete Migration Script**: See `templates/integration/qbo_client_full.j2`

---

**Document Version**: 1.0  
**Last Updated**: November 5, 2025  
**Maintained By**: QuickOdoo Team


