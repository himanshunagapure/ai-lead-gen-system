#!/usr/bin/env python3
"""
Script to create lead-related database tables
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.db.session import engine, SessionLocal
from app.models.base import Base
from app.models.extracted_lead import ExtractedLead
from app.models.lead_score import LeadScore
from app.models.crawled_content import CrawledContent

def create_tables():
    """Create all lead-related tables"""
    try:
        print("🔧 Creating lead-related database tables...")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Successfully created lead-related tables:")
        print("   - crawled_content")
        print("   - extracted_lead") 
        print("   - lead_score")
        
        # Test the connection
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT 1"))
            print("✅ Database connection test successful!")
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False
    
    return True

def check_tables():
    """Check if tables exist"""
    try:
        db = SessionLocal()
        tables = []
        
        # Check for each table
        for table_name in ['crawled_content', 'extracted_lead', 'lead_score']:
            try:
                result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                tables.append((table_name, True, count))
            except Exception:
                tables.append((table_name, False, 0))
        
        db.close()
        
        print("\n📊 Table Status:")
        for table_name, exists, count in tables:
            status = "✅" if exists else "❌"
            print(f"   {status} {table_name}: {'EXISTS' if exists else 'MISSING'} ({count} records)")
        
        return all(exists for _, exists, _ in tables)
        
    except Exception as e:
        print(f"❌ Failed to check tables: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Lead Database Setup")
    print("=" * 40)
    
    # Create tables
    if create_tables():
        print("\n" + "=" * 40)
        # Check tables
        check_tables()
        print("\n✅ Lead database setup completed!")
    else:
        print("\n❌ Lead database setup failed!")
        sys.exit(1) 