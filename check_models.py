"""Check what models are registered"""
from dotenv import load_dotenv
load_dotenv()

from app import create_app, db
app = create_app()

with app.app_context():
    print("Tables in metadata:")
    for table_name in sorted(db.metadata.tables.keys()):
        print(f"  - {table_name}")
    print(f"\nTotal tables: {len(db.metadata.tables)}")
