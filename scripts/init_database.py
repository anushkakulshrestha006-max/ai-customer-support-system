"""
Database Initialization Script for NovaStore AI Customer Support System.
Creates required tables (customers, conversations, tickets) if they do not exist.
Preserves existing data without dropping or resetting tables.
Can be executed safely as a cloud build/release step or during initial deployment:
    python scripts/init_database.py [--seed]
"""
import sys
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.database.connection import engine, SessionLocal, Base
from app.database.models import Customer, Conversation, Ticket

SAMPLE_CUSTOMERS = [
    {"name": "Alice Sharma", "email": "alice.sharma@example.com"},
    {"name": "Bob Miller", "email": "bob.miller@example.com"},
    {"name": "Carol Davis", "email": "carol.davis@example.com"},
    {"name": "David Wilson", "email": "david.wilson@example.com"},
]


def init_database(seed: bool = False):
    print("=" * 60)
    print("NovaStore Support — Database Initialization")
    print("=" * 60)

    # 1. Create tables if they do not exist (idempotent, non-destructive)
    print("Verifying database schema...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[+] Tables (customers, conversations, tickets) verified successfully.")
    except Exception as e:
        print(f"[!] Database connection error: {e}")
        print("    Please verify your MySQL host, port, credentials, and network connectivity.")
        sys.exit(1)

    # 2. Optionally seed initial demo customers if not already present
    if seed:
        print("\nVerifying seed customer profiles...")
        db = SessionLocal()
        try:
            added = 0
            for cust_data in SAMPLE_CUSTOMERS:
                existing = db.query(Customer).filter(Customer.email == cust_data["email"]).first()
                if not existing:
                    new_cust = Customer(name=cust_data["name"], email=cust_data["email"])
                    db.add(new_cust)
                    added += 1
                    print(f"  + Created customer: {cust_data['name']} ({cust_data['email']})")
                else:
                    print(f"  * Existing customer verified: {cust_data['name']} ({cust_data['email']})")
            db.commit()
            print(f"[+] Seeding complete: {added} new customer(s) added.")
            total = db.query(Customer).count()
            print(f"[+] Total registered customers in database: {total}")
        except Exception as e:
            db.rollback()
            print(f"[!] Error verifying seed data: {e}")
            sys.exit(1)
        finally:
            db.close()

    print("\nDatabase is ready for service.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize database tables safely.")
    parser.add_argument("--seed", action="store_true", help="Seed initial demo customers if not present.")
    args = parser.parse_args()
    init_database(seed=args.seed)
