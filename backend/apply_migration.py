from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables
load_dotenv()

def apply_migration():
    try:
        # Get database URL from environment
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise Exception("DATABASE_URL environment variable not found")

        # Connect to the database
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Create a cursor
        cur = conn.cursor()
        
        # Execute the migration
        cur.execute("""
            ALTER TABLE orders 
            ADD COLUMN IF NOT EXISTS error TEXT,
            ADD COLUMN IF NOT EXISTS executed_price DECIMAL(10,2),
            ADD COLUMN IF NOT EXISTS executed_at TIMESTAMP WITH TIME ZONE;
        """)
        
        # Close cursor and connection
        cur.close()
        conn.close()
        
        print("Migration applied successfully!")
        
    except Exception as e:
        print(f"Error applying migration: {str(e)}")

if __name__ == "__main__":
    apply_migration()
