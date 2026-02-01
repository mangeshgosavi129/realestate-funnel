
import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.append(os.getcwd())

from server.database import SessionLocal
from server.models import Organization, WhatsAppIntegration

def fix_integration():
    db = SessionLocal()
    try:
        # Find Tech Solutions Inc
        org = db.query(Organization).filter(Organization.name == "Tech Solutions Inc").first()
        if not org:
            print("❌ Tech Solutions Inc organization not found!")
            return

        print(f"Found Org: {org.name} ({org.id})")
        
        # Find Integration
        integration = db.query(WhatsAppIntegration).filter(WhatsAppIntegration.organization_id == org.id).first()
        if integration:
            print(f"Current Phone ID: {integration.phone_number_id}")
            integration.phone_number_id = "123123"
            db.commit()
            print(f"✅ Updated Phone ID to: {integration.phone_number_id}")
        else:
            print("❌ No WhatsApp Integration found for this org!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    fix_integration()
