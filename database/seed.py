"""
Seed script to initialize MySQL database and insert initial demo customers.
Can be executed directly: python database/seed.py
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database.connection import engine, SessionLocal, Base
from app.database.models import Customer, Ticket, Conversation


SAMPLE_CUSTOMERS = [
    {"name": "Alice Sharma", "email": "alice.sharma@example.com"},
    {"name": "Bob Miller", "email": "bob.miller@example.com"},
    {"name": "Carol Davis", "email": "carol.davis@example.com"},
    {"name": "David Wilson", "email": "david.wilson@example.com"},
]


def seed_database():
    print("=" * 50)
    print("Starting MySQL Database Initialization & Seeding...")
    print("=" * 50)

    # 1. Create tables if they do not exist
    print("Creating tables (customers, conversations, tickets)...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

    # 2. Seed initial demo customers
    db = SessionLocal()
    try:
        added_count = 0
        for cust_data in SAMPLE_CUSTOMERS:
            existing = db.query(Customer).filter(Customer.email == cust_data["email"]).first()
            if not existing:
                new_customer = Customer(name=cust_data["name"], email=cust_data["email"])
                db.add(new_customer)
                added_count += 1
                print(f"  + Added customer: {cust_data['name']} ({cust_data['email']})")
            else:
                print(f"  * Customer already exists: {cust_data['name']} ({cust_data['email']})")

        db.commit()
        print(f"\nSeeding complete! {added_count} new customer(s) added.")

        # Show total customers
        total = db.query(Customer).count()
        print(f"Total customers in database: {total}")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
