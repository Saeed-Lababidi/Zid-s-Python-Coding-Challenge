"""
Core models for shipment management.
"""
import uuid
from django.db import models
from .enums import UnifiedStatus, CourierProvider, Priority


class Shipment(models.Model):
    """
    Shipment model storing all shipment data.
    Uses JSONField for flexible sender/recipient/package data.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reference_number = models.CharField(max_length=100, db_index=True)
    waybill_number = models.CharField(max_length=100, unique=True, db_index=True)
    tracking_number = models.CharField(max_length=100, blank=True, db_index=True)

    courier_provider = models.CharField(
        max_length=50,
        choices=[(p.value, p.value) for p in CourierProvider],
        db_index=True
    )
    status = models.CharField(
        max_length=50,
        choices=[(s.value, s.value) for s in UnifiedStatus],
        default=UnifiedStatus.PENDING.value,
        db_index=True
    )
    priority = models.CharField(
        max_length=20,
        choices=[(p.value, p.value) for p in Priority],
        default=Priority.STANDARD.value
    )

    # JSONB fields for flexible data
    sender_data = models.JSONField(default=dict)
    recipient_data = models.JSONField(default=dict)
    package_data = models.JSONField(default=dict)
    courier_specific_data = models.JSONField(default=dict, blank=True)

    # Service details
    service_type = models.CharField(max_length=50, blank=True)
    special_instructions = models.TextField(blank=True)

    # COD and Insurance
    cod_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cod_currency = models.CharField(max_length=3, default="SAR")
    insurance_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Delivery info
    estimated_delivery_date = models.DateTimeField(null=True, blank=True)
    actual_delivery_date = models.DateTimeField(null=True, blank=True)

    # Cost
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(max_length=3, default="SAR")

    # Label
    label_url = models.URLField(blank=True)
    label_data = models.TextField(blank=True)

    # Status tracking
    last_status_update = models.DateTimeField(auto_now=True)
    last_status_description = models.TextField(blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["courier_provider", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.waybill_number} ({self.courier_provider})"


class TrackingEvent(models.Model):
    """
    Individual tracking events for a shipment.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    shipment = models.ForeignKey(
        Shipment,
        on_delete=models.CASCADE,
        related_name="tracking_events"
    )

    status = models.CharField(
        max_length=50,
        choices=[(s.value, s.value) for s in UnifiedStatus]
    )
    raw_status = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    details = models.TextField(blank=True)

    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]
        indexes = [
            models.Index(fields=["shipment", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.shipment.waybill_number} - {self.status} at {self.timestamp}"
