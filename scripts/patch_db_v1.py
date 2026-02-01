
import sys
import os
sys.path.append(os.getcwd())

from sqlalchemy import text
from server.database import engine

def patch_db():
    print("🔄 Patching Database Schema...")
    
    commands = [
        "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS business_name TEXT;",
        "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS business_description TEXT;",
        "ALTER TABLE organizations ADD COLUMN IF NOT EXISTS flow_prompt TEXT;"
    ]
    
    with engine.connect() as conn:
        for cmd in commands:
            try:
                print(f"Executing: {cmd}")
                conn.execute(text(cmd))
                print("✅ Success")
            except Exception as e:
                print(f"⚠️ Error (ignoring): {e}")
        conn.commit()
    
    print("✅ Patch Complete.")

if __name__ == "__main__":
    patch_db()
