#!/usr/bin/env python
"""Quick script to count activation codes in database."""
import sys
from api.deps import get_db
from api.models.licensing import ActivationCode

try:
    db = next(get_db())
    count = db.query(ActivationCode).count()
    print(f"Total Activation Codes in database: {count}")
    
    # Also show some details
    if count > 0:
        codes = db.query(ActivationCode).limit(5).all()
        print(f"\nSample codes (first 5):")
        for code in codes:
            print(f"  ID: {code.id}, Code: {code.code_plain}, Created: {code.created_at}, Tenant ID: {code.tenant_id}")
    
    db.close()
    sys.exit(0)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)

