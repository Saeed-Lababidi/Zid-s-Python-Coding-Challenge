"""
Data Transfer Objects (DTOs) for courier operations.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class Address:
    """Address DTO."""
    name: str
    address_line1: str
    city: str
    country: str
    phone: str
    postal_code: str = ""
    address_line2: str = ""
    email: str = ""
    id_no: str = ""
    po_box: str = ""
    phone2: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "postal_code": self.postal_code,
            "country": self.country,
            "phone": self.phone,
            "phone2": self.phone2,
            "email": self.email,
            "id_no": self.id_no,
            "po_box": self.po_box,
        }


@dataclass
class PackageDetails:
    """Package details DTO."""
    weight: float
    description: str
    length: float = 0.0
    width: float = 0.0
    height: float = 0.0
    value: float = 0.0
    pieces: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "weight": self.weight,
            "length": self.length,
            "width": self.width,
            "height": self.height,
            "description": self.description,
            "value": self.value,
            "pieces": self.pieces,
        }


@dataclass
class ShipmentRequest:
    """Unified shipment creation request."""
    reference_number: str
    sender: Address
    recipient: Address
    package: PackageDetails
    priority: str = "STANDARD"
    service_type: str = ""
    special_instructions: str = ""
    cod_amount: float = 0.0
    cod_currency: str = "SAR"
    insurance_amount: float = 0.0
    preferred_delivery_date: str = ""
    return_required: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ShipmentResponse:
    """Unified shipment creation response."""
    success: bool
    waybill_number: str
    tracking_number: str
    reference_number: str
    courier_provider: str
    service_type: str = ""
    estimated_delivery_date: Optional[datetime] = None
    cost: float = 0.0
    currency: str = "SAR"
    label_url: str = ""
    label_data: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    courier_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrackingEvent:
    """Single tracking event."""
    timestamp: datetime
    status: str
    description: str
    location: str = ""
    details: str = ""
    raw_status: str = ""


@dataclass
class TrackingResponse:
    """Unified tracking response."""
    success: bool
    waybill_number: str
    tracking_number: str
    status: str
    status_description: str
    last_updated: datetime
    estimated_delivery_date: Optional[datetime] = None
    location: str = ""
    events: List[TrackingEvent] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


@dataclass
class CancelResponse:
    """Unified cancellation response."""
    success: bool
    waybill_number: str
    cancellation_id: str = ""
    refund_amount: float = 0.0
    currency: str = "SAR"
    errors: List[str] = field(default_factory=list)


@dataclass
class LabelResponse:
    """Unified label response."""
    success: bool
    waybill_number: str
    label_url: str = ""
    label_data: str = ""
    format: str = "PDF"
    errors: List[str] = field(default_factory=list)
