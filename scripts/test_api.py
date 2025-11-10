#!/usr/bin/env python3
"""
Simple script to test the SEO SaaS API.

Usage:
    python scripts/test_api.py
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api/v1"


def print_response(response: requests.Response) -> None:
    """Pretty print API response."""
    print(f"\nStatus: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)


def test_health_check() -> None:
    """Test health check endpoint."""
    print("\n" + "=" * 50)
    print("Testing Health Check")
    print("=" * 50)

    response = requests.get("http://localhost:8000/health")
    print_response(response)


def test_create_project() -> Dict[str, Any]:
    """Test project creation."""
    print("\n" + "=" * 50)
    print("Testing Create Project")
    print("=" * 50)

    project_data = {
        "name": "Test Website",
        "domain": "https://example.com",
        "description": "Test project for API demonstration",
        "js_enabled": False,
        "max_depth": 3,
        "max_pages": 100,
        "crawl_delay": 1.0,
        "respect_robots": True,
    }

    response = requests.post(f"{BASE_URL}/projects/", json=project_data)
    print_response(response)

    if response.status_code == 201:
        return response.json()
    return {}


def test_list_projects() -> None:
    """Test listing projects."""
    print("\n" + "=" * 50)
    print("Testing List Projects")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/projects/")
    print_response(response)


def test_get_project(project_id: int) -> None:
    """Test getting a specific project."""
    print("\n" + "=" * 50)
    print(f"Testing Get Project {project_id}")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/projects/{project_id}")
    print_response(response)


def test_start_crawl(project_id: int) -> Dict[str, Any]:
    """Test starting a crawl job."""
    print("\n" + "=" * 50)
    print(f"Testing Start Crawl for Project {project_id}")
    print("=" * 50)

    crawl_data = {
        "project_id": project_id,
        "mode": "fast",
        "config": {"depth": 2, "max_pages": 50},
    }

    response = requests.post(f"{BASE_URL}/crawl/", json=crawl_data)
    print_response(response)

    if response.status_code == 201:
        return response.json()
    return {}


def test_get_crawl_job(job_id: int) -> None:
    """Test getting crawl job status."""
    print("\n" + "=" * 50)
    print(f"Testing Get Crawl Job {job_id}")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/crawl/{job_id}")
    print_response(response)


def test_list_pages(project_id: int) -> None:
    """Test listing pages."""
    print("\n" + "=" * 50)
    print(f"Testing List Pages for Project {project_id}")
    print("=" * 50)

    response = requests.get(f"{BASE_URL}/pages/?project_id={project_id}&limit=10")
    print_response(response)


def test_update_project(project_id: int) -> None:
    """Test updating a project."""
    print("\n" + "=" * 50)
    print(f"Testing Update Project {project_id}")
    print("=" * 50)

    update_data = {"name": "Updated Test Website", "max_pages": 200}

    response = requests.put(f"{BASE_URL}/projects/{project_id}", json=update_data)
    print_response(response)


def main():
    """Run all API tests."""
    print("\n🚀 Starting API Tests")
    print("=" * 50)

    try:
        # Test health
        test_health_check()

        # Test project endpoints
        project = test_create_project()
        if not project:
            print("\n❌ Failed to create project. Exiting.")
            return

        project_id = project["id"]

        test_list_projects()
        test_get_project(project_id)
        test_update_project(project_id)

        # Test crawl endpoints
        crawl_job = test_start_crawl(project_id)
        if crawl_job:
            job_id = crawl_job["id"]
            test_get_crawl_job(job_id)

            # Wait a bit and check again
            print("\n⏳ Waiting 5 seconds before checking job status again...")
            time.sleep(5)
            test_get_crawl_job(job_id)

        # Test page endpoints
        test_list_pages(project_id)

        print("\n" + "=" * 50)
        print("✅ All tests completed!")
        print("=" * 50)

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API at", BASE_URL)
        print("Make sure the backend is running: docker-compose up backend")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
