"""Webhook delivery service for sending HTTP notifications."""

import asyncio
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.webhook import Webhook, WebhookDelivery


class WebhookDeliveryService:
    """
    Service for delivering webhook notifications.

    Features:
    - Asynchronous HTTP requests
    - HMAC signature for security
    - Automatic retries with exponential backoff
    - Delivery logging and tracking
    - Timeout handling
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize webhook delivery service.

        Args:
            db: Database session
        """
        self.db = db

    async def deliver(
        self,
        webhook: Webhook,
        event_type: str,
        payload: Dict[str, Any],
        event_id: Optional[str] = None,
    ) -> WebhookDelivery:
        """
        Deliver a webhook notification.

        Args:
            webhook: Webhook configuration
            event_type: Type of event (e.g., "crawl.completed")
            payload: Event payload data
            event_id: Optional event identifier

        Returns:
            WebhookDelivery record
        """
        # Create delivery record
        delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=event_type,
            event_id=event_id or str(uuid.uuid4()),
            payload=payload,
            attempt_number=1,
        )

        # Build request
        headers = self._build_headers(webhook, payload, event_type)
        delivery.headers = headers

        # Send request
        start_time = datetime.utcnow()
        try:
            async with httpx.AsyncClient(timeout=webhook.timeout) as client:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                )

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Record response
            delivery.status_code = response.status_code
            delivery.response_body = response.text[:10000]  # Limit size
            delivery.response_headers = dict(response.headers)
            delivery.duration_ms = duration_ms
            delivery.delivered_at = datetime.utcnow()

            # Check if successful (2xx status code)
            if 200 <= response.status_code < 300:
                delivery.success = True
            else:
                delivery.success = False
                delivery.error_message = f"HTTP {response.status_code}: {response.text[:500]}"

                # Schedule retry if configured
                if delivery.attempt_number < webhook.max_retries:
                    delivery.next_retry_at = self._calculate_retry_time(
                        delivery.attempt_number, webhook.retry_delay
                    )

        except httpx.TimeoutException as e:
            delivery.success = False
            delivery.error_message = f"Request timeout after {webhook.timeout}s"
            delivery.delivered_at = datetime.utcnow()
            delivery.duration_ms = webhook.timeout * 1000

            # Schedule retry
            if delivery.attempt_number < webhook.max_retries:
                delivery.next_retry_at = self._calculate_retry_time(
                    delivery.attempt_number, webhook.retry_delay
                )

        except Exception as e:
            delivery.success = False
            delivery.error_message = f"Delivery failed: {str(e)}"
            delivery.delivered_at = datetime.utcnow()

            # Schedule retry
            if delivery.attempt_number < webhook.max_retries:
                delivery.next_retry_at = self._calculate_retry_time(
                    delivery.attempt_number, webhook.retry_delay
                )

        # Save delivery record
        self.db.add(delivery)
        await self.db.commit()
        await self.db.refresh(delivery)

        # Update webhook last triggered timestamp
        webhook.last_triggered_at = datetime.utcnow()
        await self.db.commit()

        return delivery

    async def retry(self, delivery: WebhookDelivery) -> WebhookDelivery:
        """
        Retry a failed webhook delivery.

        Args:
            delivery: Previous delivery attempt

        Returns:
            New delivery record for the retry
        """
        # Load webhook
        from sqlalchemy import select

        query = select(Webhook).where(Webhook.id == delivery.webhook_id)
        result = await self.db.execute(query)
        webhook = result.scalar_one()

        if not webhook.is_active:
            raise ValueError("Webhook is disabled")

        # Create new delivery record for retry
        new_delivery = WebhookDelivery(
            webhook_id=webhook.id,
            event_type=delivery.event_type,
            event_id=delivery.event_id,
            payload=delivery.payload,
            attempt_number=delivery.attempt_number + 1,
        )

        # Build headers
        headers = self._build_headers(webhook, delivery.payload, delivery.event_type)
        new_delivery.headers = headers

        # Send request
        start_time = datetime.utcnow()
        try:
            async with httpx.AsyncClient(timeout=webhook.timeout) as client:
                response = await client.post(
                    webhook.url,
                    json=delivery.payload,
                    headers=headers,
                )

            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Record response
            new_delivery.status_code = response.status_code
            new_delivery.response_body = response.text[:10000]
            new_delivery.response_headers = dict(response.headers)
            new_delivery.duration_ms = duration_ms
            new_delivery.delivered_at = datetime.utcnow()

            if 200 <= response.status_code < 300:
                new_delivery.success = True
            else:
                new_delivery.success = False
                new_delivery.error_message = f"HTTP {response.status_code}: {response.text[:500]}"

                # Schedule next retry if needed
                if new_delivery.attempt_number < webhook.max_retries:
                    new_delivery.next_retry_at = self._calculate_retry_time(
                        new_delivery.attempt_number, webhook.retry_delay
                    )

        except Exception as e:
            new_delivery.success = False
            new_delivery.error_message = f"Retry failed: {str(e)}"
            new_delivery.delivered_at = datetime.utcnow()

            # Schedule next retry
            if new_delivery.attempt_number < webhook.max_retries:
                new_delivery.next_retry_at = self._calculate_retry_time(
                    new_delivery.attempt_number, webhook.retry_delay
                )

        # Save new delivery record
        self.db.add(new_delivery)
        await self.db.commit()
        await self.db.refresh(new_delivery)

        return new_delivery

    def _build_headers(
        self, webhook: Webhook, payload: Dict[str, Any], event_type: str
    ) -> Dict[str, str]:
        """
        Build HTTP headers for webhook request.

        Args:
            webhook: Webhook configuration
            payload: Event payload
            event_type: Event type

        Returns:
            Headers dictionary
        """
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SEO-SaaS-Webhook/1.0",
            "X-Webhook-Event": event_type,
            "X-Webhook-ID": str(webhook.id),
            "X-Webhook-Timestamp": str(int(datetime.utcnow().timestamp())),
        }

        # Add HMAC signature if secret is configured
        if webhook.secret:
            signature = self._generate_signature(payload, webhook.secret)
            headers["X-Webhook-Signature"] = signature

        # Add custom headers
        if webhook.custom_headers:
            headers.update(webhook.custom_headers)

        return headers

    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """
        Generate HMAC SHA256 signature for payload.

        Args:
            payload: Event payload
            secret: Webhook secret key

        Returns:
            Hex-encoded HMAC signature
        """
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        signature = hmac.new(
            secret.encode("utf-8"), payload_bytes, hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    def _calculate_retry_time(self, attempt: int, base_delay: int) -> datetime:
        """
        Calculate next retry time with exponential backoff.

        Args:
            attempt: Current attempt number
            base_delay: Base delay in seconds

        Returns:
            Datetime for next retry
        """
        # Exponential backoff: base_delay * 2^(attempt-1)
        delay_seconds = base_delay * (2 ** (attempt - 1))

        # Cap at 1 hour
        delay_seconds = min(delay_seconds, 3600)

        return datetime.utcnow() + timedelta(seconds=delay_seconds)

    async def process_pending_retries(self):
        """
        Process all pending webhook retries.

        This method should be called periodically (e.g., by a background worker)
        to retry failed deliveries.
        """
        from sqlalchemy import select

        # Get all deliveries that need retry
        query = (
            select(WebhookDelivery)
            .where(
                WebhookDelivery.success == False,
                WebhookDelivery.next_retry_at.isnot(None),
                WebhookDelivery.next_retry_at <= datetime.utcnow(),
            )
            .limit(100)  # Process in batches
        )

        result = await self.db.execute(query)
        deliveries = result.scalars().all()

        # Retry each delivery
        for delivery in deliveries:
            try:
                await self.retry(delivery)
            except Exception as e:
                # Log error but continue processing
                print(f"Failed to retry delivery {delivery.id}: {e}")

    async def get_webhook_stats(self, webhook_id: int) -> Dict[str, Any]:
        """
        Get delivery statistics for a webhook.

        Args:
            webhook_id: Webhook ID

        Returns:
            Statistics dictionary
        """
        from sqlalchemy import select, func

        # Total deliveries
        total_query = select(func.count()).select_from(WebhookDelivery).where(
            WebhookDelivery.webhook_id == webhook_id
        )
        result = await self.db.execute(total_query)
        total_deliveries = result.scalar() or 0

        # Successful deliveries
        success_query = select(func.count()).select_from(WebhookDelivery).where(
            WebhookDelivery.webhook_id == webhook_id,
            WebhookDelivery.success == True,
        )
        result = await self.db.execute(success_query)
        successful_deliveries = result.scalar() or 0

        # Failed deliveries
        failed_deliveries = total_deliveries - successful_deliveries

        # Success rate
        success_rate = (
            (successful_deliveries / total_deliveries * 100)
            if total_deliveries > 0
            else 0
        )

        # Average response time
        avg_time_query = select(func.avg(WebhookDelivery.duration_ms)).where(
            WebhookDelivery.webhook_id == webhook_id,
            WebhookDelivery.duration_ms.isnot(None),
        )
        result = await self.db.execute(avg_time_query)
        avg_response_time = result.scalar() or 0

        return {
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful_deliveries,
            "failed_deliveries": failed_deliveries,
            "success_rate": round(success_rate, 2),
            "avg_response_time_ms": round(avg_response_time, 2),
        }
