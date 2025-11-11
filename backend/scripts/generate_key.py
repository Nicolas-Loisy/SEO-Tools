#!/usr/bin/env python3
"""
Generate a new API key for existing tenant.

Usage:
    python scripts/generate_key.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import generate_api_key, hash_api_key, get_key_prefix
from app.models.tenant import Tenant
from app.models.api_key import APIKey


def generate_new_key():
    """Generate a new API key."""
    print("🔑 SEO SaaS - API Key Generator")
    print("=" * 50)
    print()

    # Create database connection
    db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Get first active tenant
        tenant = db.query(Tenant).filter(Tenant.is_active == True).first()

        if not tenant:
            print("❌ No active tenant found!")
            print("   Run bootstrap.py first to create a tenant.")
            return 1

        print(f"👤 Tenant: {tenant.name} (ID: {tenant.id})")
        print()

        # Ask for key name
        key_name = input("Enter a name for this key (default: 'New Key'): ").strip()
        if not key_name:
            key_name = "New Key"

        # Ask for scopes
        print()
        print("Available scopes: read, write, admin")
        scopes = input("Enter scopes (comma-separated, default: 'read,write'): ").strip()
        if not scopes:
            scopes = "read,write"

        print()
        print("🔐 Generating API key...")

        # Generate API key
        raw_key = generate_api_key()
        key_hash = hash_api_key(raw_key)
        key_prefix = get_key_prefix(raw_key)

        api_key = APIKey(
            tenant_id=tenant.id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=key_name,
            description=f"Generated via generate_key.py",
            scopes=scopes,
            is_active=True,
        )

        db.add(api_key)
        db.commit()

        print("✓ API key created!")
        print()
        print("=" * 50)
        print("🎉 SUCCESS!")
        print("=" * 50)
        print()
        print("📝 Your NEW API Key (save this now!):")
        print()
        print(f"    {raw_key}")
        print()
        print("=" * 50)
        print()
        print("🔧 Key Details:")
        print(f"   Name:   {key_name}")
        print(f"   Scopes: {scopes}")
        print(f"   Prefix: {key_prefix}")
        print()
        print("💡 Use this key in your frontend or API requests:")
        print(f"   curl -H 'X-API-Key: {raw_key[:20]}...' \\")
        print("        http://localhost:8000/api/v1/usage/quota")
        print()

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(generate_new_key())
