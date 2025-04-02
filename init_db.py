import os
from dotenv import load_dotenv
from database import init_db, engine
from alembic.config import Config
from alembic import command

def main():
    # Load environment variables
    load_dotenv()
    
    # Initialize database
    print("Initializing database...")
    init_db()
    
    # Run migrations
    print("Running database migrations...")
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    
    print("Database initialization complete!")

if __name__ == "__main__":
    main() 