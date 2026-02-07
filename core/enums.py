"""
Unified Status Enum for all couriers.
"""
from enum import Enum


class UnifiedStatus(str, Enum):
    """Unified shipment status across all courier providers."""
    PENDING = "PENDING"
    CREATED = "CREATED"
    CONFIRMED = "CONFIRMED"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    FAILED_DELIVERY = "FAILED_DELIVERY"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"
    EXCEPTION = "EXCEPTION"
    LOST = "LOST"
    DAMAGED = "DAMAGED"


class CourierProvider(str, Enum):
    """Supported courier providers."""
    SMSA = "SMSA"
    ARAMEX = "ARAMEX"
    MOCK = "MOCK"


class Priority(str, Enum):
    """Shipment priority levels."""
    STANDARD = "STANDARD"
    EXPRESS = "EXPRESS"
    PRIORITY = "PRIORITY"
