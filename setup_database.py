#!/usr/bin/env python3
"""
Database setup script to create all tables
"""
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.db.base import Base
from app.db.session import engine

def setup_database():
    """Create all database tables"""
    print("🔧 Setting up database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All database tables created successfully!")
        
        # Test connection
        from app.db.session import test_db_connection
        test_db_connection()
        
        print("✅ Database setup completed!")
        return True
        
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

if __name__ == "__main__":
    setup_database() 