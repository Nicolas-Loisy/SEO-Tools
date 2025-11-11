"""Webhook event dispatcher for triggering notifications."""

import asyncio
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.webhook import Webhook
from app.services.webhook_delivery import WebhookDeliveryService


class WebhookDispatcher:
    """
    Dispatcher for webhook events.

    Handles:
    - Event filtering by subscription
    - Async delivery to multiple webhooks
    - Event payload construction
    """

    # Supported event types
    EVENTS = {
        "crawl.started": "Crawl job has started",
        "crawl.completed": "Crawl job completed successfully",
        "crawl.failed": "Crawl job failed",
        "analysis.completed": "Analysis completed",
        "content.generated": "Content generation completed",
        "quota.warning": "Approaching quota limit (80%)",
        "quota.exceeded": "Quota limit exceeded",
        "project.created": "Project created",
        "project.deleted": "Project deleted",
        "tree.generated": "Site tree generated",
    }

    def __init__(self, db: AsyncSession):
        """
        Initialize webhook dispatcher.

        Args:
            db: Database session
        """
        self.db = db
        self.delivery_service = WebhookDeliveryService(db)

    async def dispatch(
        self,
        tenant_id: int,
        event_type: str,
        payload: Dict[str, Any],
        event_id: Optional[str] = None,
    ) -> List[int]:
        """
        Dispatch an event to all subscribed webhooks.

        Args:
            tenant_id: Tenant ID
            event_type: Event type (e.g., "crawl.completed")
            payload: Event payload data
            event_id: Optional event identifier

        Returns:
            List of delivery IDs
        """
        # Validate event type
        if event_type not in self.EVENTS:
            raise ValueError(f"Unknown event type: {event_type}")

        # Get all active webhooks for this tenant subscribed to this event
        query = (
            select(Webhook)
            .where(
                Webhook.tenant_id == tenant_id,
                Webhook.is_active == True,
            )
        )
        result = await self.db.execute(query)
        webhooks = result.scalars().all()

        # Filter webhooks subscribed to this event
        subscribed_webhooks = [
            webhook for webhook in webhooks if event_type in webhook.events
        ]

        if not subscribed_webhooks:
            return []

        # Enrich payload with standard fields
        enriched_payload = self._enrich_payload(payload, event_type, tenant_id)

        # Deliver to all subscribed webhooks asynchronously
        delivery_tasks = [
            self.delivery_service.deliver(
                webhook=webhook,
                event_type=event_type,
                payload=enriched_payload,
                event_id=event_id,
            )
            for webhook in subscribed_webhooks
        ]

        deliveries = await asyncio.gather(*delivery_tasks, return_exceptions=True)

        # Return delivery IDs (filter out exceptions)
        delivery_ids = [
            delivery.id for delivery in deliveries
            if not isinstance(delivery, Exception)
        ]

        return delivery_ids

    def _enrich_payload(
        self, payload: Dict[str, Any], event_type: str, tenant_id: int
    ) -> Dict[str, Any]:
        """
        Enrich payload with standard fields.

        Args:
            payload: Original payload
            event_type: Event type
            tenant_id: Tenant ID

        Returns:
            Enriched payload
        """
        from datetime import datetime

        enriched = {
            "event": event_type,
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload,
        }

        return enriched

    # Convenience methods for common events

    async def dispatch_crawl_started(
        self, tenant_id: int, crawl_job_id: int, project_id: int, mode: str
    ):
        """Dispatch crawl.started event."""
        payload = {
            "crawl_job_id": crawl_job_id,
            "project_id": project_id,
            "mode": mode,
        }
        return await self.dispatch(
            tenant_id=tenant_id,
            event_type="crawl.started",
            payload=payload,
            event_id=f"crawl_{crawl_job_id}",
        )

    async def dispatch_crawl_completed(
        self,
        tenant_id: int,
        crawl_job_id: int,
        project_id: int,
        pages_crawled: int,
        duration_seconds: float,
    ):
        """Dispatch crawl.completed event."""
        payload = {
            "crawl_job_id": crawl_job_id,
            "project_id": project_id,
            "pages_crawled": pages_crawled,
            "duration_seconds": duration_seconds,
        }
        return await self.dispatch(
            tenant_id=tenant_id,
            event_type="crawl.completed",
            payload=payload,
            event_id=f"crawl_{crawl_job_id}",
        )

    async def dispatch_crawl_failed(
        self, tenant_id: int, crawl_job_id: int, project_id: int, error_message: str
    ):
        """Dispatch crawl.failed event."""
        payload = {
            "crawl_job_id": crawl_job_id,
            "project_id": project_id,
            "error": error_message,
        }
        return await self.dispatch(
            tenant_id=tenant_id,
            event_type="crawl.failed",
            payload=payload,
            event_id=f"crawl_{crawl_job_id}",
        )

    async def dispatch_quota_warning(
        self, tenant_id: int, usage_percent: float, quota_type: str
    ):
        """Dispatch quota.warning event."""
        payload = {
            "quota_type": quota_type,
            "usage_percent": usage_percent,
            "message": f"You have used {usage_percent}% of your {quota_type} quota",
        }
        return await self.dispatch(
            tenant_id=tenant_id,
            event_type="quota.warning",
            payload=payload,
        )

    async def dispatch_quota_exceeded(
        self, tenant_id: int, quota_type: str, current_usage: int, limit: int
    ):
        """Dispatch quota.exceeded event."""
        payload = {
            "quota_type": quota_type,
            "current_usage": current_usage,
            "limit": limit,
            "message": f"Quota exceeded: {current_usage}/{limit} {quota_type}",
        }
        return await self.dispatch(
            tenant_id=tenant_id,
            event_type="quota.exceeded",
            payload=payload,
        )

    async def dispatch_content_generated(
        self, tenant_id: int, content_type: str, page_id: Optional[int] = None
    ):
        """Dispatch content.generated event."""
        payload = {
            "content_type": content_type,
            "page_id": page_id,
        }
        return await self.dispatch(
            tenant_id=tenant_id,
            event_type="content.generated",
            payload=payload,
        )

    async def dispatch_tree_generated(
        self, tenant_id: int, tree_id: int, project_id: Optional[int] = None
    ):
        """Dispatch tree.generated event."""
        payload = {
            "tree_id": tree_id,
            "project_id": project_id,
        }
        return await self.dispatch(
            tenant_id=tenant_id,
            event_type="tree.generated",
            payload=payload,
            event_id=f"tree_{tree_id}",
        )

    async def dispatch_project_created(self, tenant_id: int, project_id: int, name: str):
        """Dispatch project.created event."""
        payload = {
            "project_id": project_id,
            "name": name,
        }
        return await self.dispatch(
            tenant_id=tenant_id,
            event_type="project.created",
            payload=payload,
            event_id=f"project_{project_id}",
        )

    async def dispatch_project_deleted(self, tenant_id: int, project_id: int):
        """Dispatch project.deleted event."""
        payload = {
            "project_id": project_id,
        }
        return await self.dispatch(
            tenant_id=tenant_id,
            event_type="project.deleted",
            payload=payload,
            event_id=f"project_{project_id}",
        )

    async def dispatch_analysis_completed(
        self, tenant_id: int, project_id: int, analysis_type: str
    ):
        """Dispatch analysis.completed event."""
        payload = {
            "project_id": project_id,
            "analysis_type": analysis_type,
        }
        return await self.dispatch(
            tenant_id=tenant_id,
            event_type="analysis.completed",
            payload=payload,
        )

    @classmethod
    def get_available_events(cls) -> Dict[str, str]:
        """
        Get list of available event types with descriptions.

        Returns:
            Dictionary of event types and descriptions
        """
        return cls.EVENTS.copy()
