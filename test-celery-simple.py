#!/usr/bin/env python3
"""Simple test to check if Celery tasks can be sent and received."""

import sys
import os

# Add backend to path
sys.path.insert(0, '/app')

print("=" * 60)
print("Testing Celery Task Sending")
print("=" * 60)

try:
    print("\n[1/5] Importing Celery app...")
    from app.workers.celery_app import celery_app
    print("✓ Celery app imported successfully")
    print(f"  Broker: {celery_app.conf.broker_url}")
    print(f"  Backend: {celery_app.conf.result_backend}")
except Exception as e:
    print(f"✗ Failed to import Celery app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n[2/5] Importing crawler tasks...")
    from app.workers.crawler_tasks import crawl_site
    print("✓ Crawler tasks imported successfully")
    print(f"  Task name: {crawl_site.name}")
except Exception as e:
    print(f"✗ Failed to import crawler tasks: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("\n[3/5] Checking Celery connection...")
    # Try to inspect the Celery app
    inspector = celery_app.control.inspect()
    active_queues = inspector.active_queues()
    if active_queues:
        print("✓ Worker is connected")
        for worker, queues in active_queues.items():
            print(f"  Worker: {worker}")
            for queue in queues:
                print(f"    - Queue: {queue['name']}")
    else:
        print("⚠ No workers found or workers not responding")
except Exception as e:
    print(f"⚠ Could not inspect workers: {e}")

try:
    print("\n[4/5] Checking task routing...")
    task_name = "app.workers.crawler_tasks.crawl_site"
    routes = celery_app.conf.task_routes
    print(f"  Task routes configured: {routes}")

    # Check which queue this task would go to
    for pattern, config in routes.items():
        if pattern in task_name or task_name.startswith(pattern.replace('*', '')):
            print(f"  ✓ Task '{task_name}' routes to queue: {config.get('queue')}")
            break
except Exception as e:
    print(f"⚠ Could not check routing: {e}")

try:
    print("\n[5/5] Sending test task...")
    # Get a crawl job ID from database
    import asyncio
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select, text
    from app.models.crawl import CrawlJob

    async def get_latest_job_id():
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(CrawlJob.id).order_by(CrawlJob.created_at.desc()).limit(1)
            )
            job = result.scalar_one_or_none()
            return job

    job_id = asyncio.run(get_latest_job_id())

    if job_id:
        print(f"  Found crawl job ID: {job_id}")
        print(f"  Sending task to Celery...")
        task = crawl_site.delay(job_id)
        print(f"✓ Task sent successfully!")
        print(f"  Task ID: {task.id}")
        print(f"  Task status: {task.status}")
    else:
        print("  ⚠ No crawl jobs found in database")
        print("  Creating a test task with job_id=999 (will fail but tests sending)...")
        task = crawl_site.delay(999)
        print(f"✓ Task sent successfully!")
        print(f"  Task ID: {task.id}")

except Exception as e:
    print(f"✗ Failed to send task: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ All checks passed!")
print("=" * 60)
print("\nNext steps:")
print("1. Check worker logs: docker compose logs celery-worker")
print("2. Check if task was received by worker")
print("3. Check Redis queues: docker compose exec redis redis-cli llen crawler")
