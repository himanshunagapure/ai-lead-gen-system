import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()

# Update the default to MySQL; set DATABASE_URL in your .env for production
DATABASE_URL = os.getenv('DATABASE_URL')

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) 

def test_db_connection():
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))

        print("✅ Database connection successful!")
    except Exception as e:
        print("❌ Failed to connect to database:")
        print(e)
    finally:
        db.close()

# Run this only when executing the file directly
if __name__ == "__main__":
    test_db_connection()
