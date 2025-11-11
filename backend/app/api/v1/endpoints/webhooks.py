"""Webhook management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_tenant
from app.models.tenant import Tenant
from app.models.webhook import Webhook, WebhookDelivery
from app.api.v1.schemas.webhook import (
    WebhookCreateRequest,
    WebhookUpdateRequest,
    WebhookResponse,
    WebhookListResponse,
    WebhookDeliveryResponse,
    WebhookDeliveryListResponse,
    WebhookStatsResponse,
    WebhookTestRequest,
    WebhookEventsResponse,
)
from app.services.webhook_delivery import WebhookDeliveryService
from app.services.webhook_dispatcher import WebhookDispatcher

router = APIRouter()


@router.get("/events", response_model=WebhookEventsResponse)
async def get_available_events():
    """
    Get list of available webhook event types.

    Returns all event types that can be subscribed to with descriptions.
    """
    events = WebhookDispatcher.get_available_events()
    return WebhookEventsResponse(events=events)


@router.post("/", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    request: WebhookCreateRequest,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Create a new webhook endpoint.

    Webhooks receive HTTP POST notifications when subscribed events occur.
    """
    # Validate event types
    available_events = WebhookDispatcher.get_available_events()
    for event in request.events:
        if event not in available_events:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event type: {event}. Available: {list(available_events.keys())}",
            )

    # Create webhook
    webhook = Webhook(
        tenant_id=tenant.id,
        name=request.name,
        url=str(request.url),
        secret=request.secret,
        events=request.events,
        max_retries=request.max_retries,
        retry_delay=request.retry_delay,
        timeout=request.timeout,
        custom_headers=request.custom_headers or {},
        description=request.description,
    )

    db.add(webhook)
    await db.commit()
    await db.refresh(webhook)

    return webhook


@router.get("/", response_model=WebhookListResponse)
async def list_webhooks(
    skip: int = 0,
    limit: int = 50,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """List all webhooks for the current tenant."""
    query = select(Webhook).where(Webhook.tenant_id == tenant.id)

    if is_active is not None:
        query = query.where(Webhook.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar() or 0

    # Get webhooks
    query = query.offset(skip).limit(limit).order_by(Webhook.created_at.desc())
    result = await db.execute(query)
    webhooks = result.scalars().all()

    return WebhookListResponse(webhooks=webhooks, total=total)


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Get a specific webhook by ID."""
    query = select(Webhook).where(
        Webhook.id == webhook_id, Webhook.tenant_id == tenant.id
    )
    result = await db.execute(query)
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    return webhook


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    request: WebhookUpdateRequest,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Update a webhook."""
    query = select(Webhook).where(
        Webhook.id == webhook_id, Webhook.tenant_id == tenant.id
    )
    result = await db.execute(query)
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Validate events if provided
    if request.events:
        available_events = WebhookDispatcher.get_available_events()
        for event in request.events:
            if event not in available_events:
                raise HTTPException(
                    status_code=400, detail=f"Invalid event type: {event}"
                )

    # Update fields
    if request.name is not None:
        webhook.name = request.name
    if request.url is not None:
        webhook.url = str(request.url)
    if request.secret is not None:
        webhook.secret = request.secret
    if request.events is not None:
        webhook.events = request.events
    if request.is_active is not None:
        webhook.is_active = request.is_active
    if request.max_retries is not None:
        webhook.max_retries = request.max_retries
    if request.retry_delay is not None:
        webhook.retry_delay = request.retry_delay
    if request.timeout is not None:
        webhook.timeout = request.timeout
    if request.custom_headers is not None:
        webhook.custom_headers = request.custom_headers
    if request.description is not None:
        webhook.description = request.description

    await db.commit()
    await db.refresh(webhook)

    return webhook


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Delete a webhook."""
    query = select(Webhook).where(
        Webhook.id == webhook_id, Webhook.tenant_id == tenant.id
    )
    result = await db.execute(query)
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    await db.execute(delete(Webhook).where(Webhook.id == webhook_id))
    await db.commit()

    return Response(status_code=204)


@router.get("/{webhook_id}/deliveries", response_model=WebhookDeliveryListResponse)
async def list_webhook_deliveries(
    webhook_id: int,
    skip: int = 0,
    limit: int = 50,
    success: Optional[bool] = None,
    event_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """List delivery attempts for a webhook."""
    # Verify webhook belongs to tenant
    webhook_query = select(Webhook).where(
        Webhook.id == webhook_id, Webhook.tenant_id == tenant.id
    )
    result = await db.execute(webhook_query)
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Get deliveries
    query = select(WebhookDelivery).where(WebhookDelivery.webhook_id == webhook_id)

    if success is not None:
        query = query.where(WebhookDelivery.success == success)
    if event_type is not None:
        query = query.where(WebhookDelivery.event_type == event_type)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    result = await db.execute(count_query)
    total = result.scalar() or 0

    # Get deliveries
    query = query.offset(skip).limit(limit).order_by(WebhookDelivery.created_at.desc())
    result = await db.execute(query)
    deliveries = result.scalars().all()

    return WebhookDeliveryListResponse(deliveries=deliveries, total=total)


@router.get("/{webhook_id}/stats", response_model=WebhookStatsResponse)
async def get_webhook_stats(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Get delivery statistics for a webhook."""
    # Verify webhook belongs to tenant
    webhook_query = select(Webhook).where(
        Webhook.id == webhook_id, Webhook.tenant_id == tenant.id
    )
    result = await db.execute(webhook_query)
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Get stats
    delivery_service = WebhookDeliveryService(db)
    stats = await delivery_service.get_webhook_stats(webhook_id)

    return WebhookStatsResponse(**stats)


@router.post("/{webhook_id}/test", response_model=WebhookDeliveryResponse)
async def test_webhook(
    webhook_id: int,
    request: WebhookTestRequest,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """
    Test a webhook by sending a test event.

    Sends a test payload to verify the webhook endpoint is working correctly.
    """
    # Get webhook
    webhook_query = select(Webhook).where(
        Webhook.id == webhook_id, Webhook.tenant_id == tenant.id
    )
    result = await db.execute(webhook_query)
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Create test payload
    test_payload = request.test_payload or {
        "message": "This is a test webhook delivery",
        "webhook_id": webhook_id,
    }

    # Send test delivery
    delivery_service = WebhookDeliveryService(db)
    delivery = await delivery_service.deliver(
        webhook=webhook,
        event_type=request.event_type,
        payload=test_payload,
        event_id=f"test_{webhook_id}",
    )

    return delivery


@router.post("/{webhook_id}/deliveries/{delivery_id}/retry", response_model=WebhookDeliveryResponse)
async def retry_webhook_delivery(
    webhook_id: int,
    delivery_id: int,
    db: AsyncSession = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant),
):
    """Manually retry a failed webhook delivery."""
    # Verify webhook belongs to tenant
    webhook_query = select(Webhook).where(
        Webhook.id == webhook_id, Webhook.tenant_id == tenant.id
    )
    result = await db.execute(webhook_query)
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    # Get delivery
    delivery_query = select(WebhookDelivery).where(
        WebhookDelivery.id == delivery_id,
        WebhookDelivery.webhook_id == webhook_id,
    )
    result = await db.execute(delivery_query)
    delivery = result.scalar_one_or_none()

    if not delivery:
        raise HTTPException(status_code=404, detail="Delivery not found")

    if delivery.success:
        raise HTTPException(
            status_code=400, detail="Cannot retry successful delivery"
        )

    # Retry delivery
    delivery_service = WebhookDeliveryService(db)
    new_delivery = await delivery_service.retry(delivery)

    return new_delivery
