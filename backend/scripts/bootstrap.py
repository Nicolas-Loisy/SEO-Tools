#!/usr/bin/env python3
"""
Bootstrap script for initial setup of SEO SaaS Tool.

This script:
1. Creates the default tenant
2. Generates an initial API key
3. Outputs setup information

Usage:
    python scripts/bootstrap.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import generate_api_key, hash_api_key, get_key_prefix
from app.models.tenant import Tenant
from app.models.api_key import APIKey
from app.core.database import Base


def bootstrap():
    """Bootstrap the application."""
    print("🚀 SEO SaaS Tool - Bootstrap Script")
    print("=" * 50)

    # Create database connection
    db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    engine = create_engine(db_url)

    # Create pgvector extension
    print("\n🔧 Enabling pgvector extension...")
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        print("✓ pgvector extension enabled")
    except Exception as e:
        print(f"⚠️  Warning: Could not create pgvector extension: {e}")
        print("   Make sure PostgreSQL has pgvector installed")
        return 1

    # Create all tables
    print("\n📊 Creating database tables...")
    Base.metadata.create_all(engine)
    print("✓ Tables created")

    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if default tenant exists
        tenant = db.query(Tenant).filter(Tenant.slug == "default").first()

        if not tenant:
            print("\n👤 Creating default tenant...")
            tenant = Tenant(
                name="Default Organization",
                slug="default",
                plan="pro",
                max_projects=50,
                max_pages_per_crawl=10000,
                max_api_calls_per_month=100000,
                is_active=True,
            )
            db.add(tenant)
            db.flush()
            print(f"✓ Tenant created (ID: {tenant.id})")
        else:
            print(f"\n👤 Default tenant already exists (ID: {tenant.id})")

        # Check if API keys exist for tenant
        existing_keys = db.query(APIKey).filter(APIKey.tenant_id == tenant.id).count()

        if existing_keys == 0:
            print("\n🔑 Generating initial API key...")

            # Generate API key
            raw_key = generate_api_key()
            key_hash = hash_api_key(raw_key)
            key_prefix = get_key_prefix(raw_key)

            api_key = APIKey(
                tenant_id=tenant.id,
                key_hash=key_hash,
                key_prefix=key_prefix,
                name="Bootstrap Key",
                description="Initial API key created during setup",
                scopes="read,write,admin",
                is_active=True,
            )

            db.add(api_key)
            db.commit()

            print("✓ API key generated")
            print()
            print("=" * 50)
            print("🎉 SETUP COMPLETE!")
            print("=" * 50)
            print()
            print("📝 Your API Key (save this, it won't be shown again!):")
            print()
            print(f"    {raw_key}")
            print()
            print("=" * 50)
            print()
            print("🚀 Next Steps:")
            print()
            print("1. Save the API key above in a secure location")
            print("2. Use it in your requests:")
            print()
            print("   curl -H 'X-API-Key: " + raw_key[:20] + "...' \\")
            print("        http://localhost:8000/api/v1/auth/me")
            print()
            print("3. Access the API documentation:")
            print("   http://localhost:8000/docs")
            print()
            print("4. Create a project and start crawling!")
            print()

        else:
            print(f"\n🔑 Tenant already has {existing_keys} API key(s)")
            print("\n✨ Use existing API keys or create new ones via the API:")
            print("   POST /api/v1/auth/keys")

        db.commit()

    except Exception as e:
        print(f"\n❌ Error during bootstrap: {e}")
        db.rollback()
        return 1

    finally:
        db.close()

    print()
    print("✅ Bootstrap completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(bootstrap())
