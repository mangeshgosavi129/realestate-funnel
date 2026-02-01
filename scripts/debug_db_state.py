
import sys
import os
from sqlalchemy import text

# Add project root to sys.path
sys.path.append(os.getcwd())

from server.database import SessionLocal
from server.models import Organization, WhatsAppIntegration, Conversation

def debug_db():
    db = SessionLocal()
    try:
        print("\n=== ORGANIZATIONS & INTEGRATIONS ===")
        orgs = db.query(Organization).all()
        for org in orgs:
            print(f"Org: {org.name} ({org.id})")
            integrations = db.query(WhatsAppIntegration).filter(WhatsAppIntegration.organization_id == org.id).all()
            for w in integrations:
                print(f"  - Phone ID: {w.phone_number_id} (Connected: {w.is_connected})")
            if not integrations:
                print("  - No WhatsApp Integration found")

        print("\n=== FLAGGED CONVERSATIONS (Needs Human Attention) ===")
        conversations = db.query(Conversation).filter(Conversation.needs_human_attention == True).all()
        if not conversations:
             print("No conversations flagged for human attention.")
        for conv in conversations:
            print(f"Conv {conv.id} | Org: {conv.organization_id} | Lead: {conv.lead_id} | Stage: {conv.stage}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_db()
