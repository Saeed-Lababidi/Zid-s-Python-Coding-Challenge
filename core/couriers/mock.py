"""
Mock Courier implementation for testing without real API credentials.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
import uuid

from .base import CourierBase
from ..dtos import (
    ShipmentRequest,
    ShipmentResponse,
    TrackingResponse,
    TrackingEvent,
    CancelResponse,
    LabelResponse,
)
from ..enums import UnifiedStatus


logger = logging.getLogger(__name__)


class MockCourier(CourierBase):
    """
    Mock courier for testing purposes.
    Does not make real API calls - generates realistic mock responses.
    """

    # In-memory storage for mock shipments
    _shipments: Dict[str, Dict[str, Any]] = {}

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Mock courier accepts any config."""
        pass

    def get_provider_name(self) -> str:
        return "MOCK"

    def get_supported_features(self) -> List[str]:
        return ["cancellation", "cod", "insurance", "signature_required", "express", "tracking"]

    def map_status(self, raw_status: str) -> UnifiedStatus:
        try:
            return UnifiedStatus(raw_status.upper())
        except ValueError:
            return UnifiedStatus.EXCEPTION

    def create_shipment(self, request: ShipmentRequest) -> ShipmentResponse:
        """Create a mock shipment."""
        errors = self.validate_shipment_request(request)
        if errors:
            return ShipmentResponse(
                success=False,
                waybill_number="",
                tracking_number="",
                reference_number=request.reference_number,
                courier_provider=self.get_provider_name(),
                errors=errors,
            )

        # Generate mock waybill
        waybill = f"MOCK{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:4].upper()}"

        # Store in memory for tracking
        self._shipments[waybill] = {
            "request": request,
            "status": UnifiedStatus.CREATED.value,
            "created_at": datetime.now(),
            "events": [
                {
                    "timestamp": datetime.now(),
                    "status": UnifiedStatus.CREATED.value,
                    "description": "Shipment created successfully",
                    "location": request.sender.city,
                }
            ],
        }

        logger.info(f"Mock shipment created: {waybill}")

        return ShipmentResponse(
            success=True,
            waybill_number=waybill,
            tracking_number=waybill,
            reference_number=request.reference_number,
            courier_provider=self.get_provider_name(),
            service_type="MOCK_EXPRESS",
            estimated_delivery_date=datetime.now() + timedelta(days=3),
            cost=50.0,
            currency="SAR",
            label_url=f"https://mock-courier.example.com/labels/{waybill}.pdf",
            label_data="JVBERi0xLjQKMSAwIG9iago8PC9UeXBlL1BhZ2VzL0tpZHNbXC9Db3VudCAwPj4KZW5kb2Jq",  # Mock base64 PDF
            courier_data={"mock": True, "waybill": waybill},
        )

    def track_shipment(self, waybill_number: str) -> TrackingResponse:
        """Track a mock shipment."""
        shipment_data = self._shipments.get(waybill_number)

        if not shipment_data:
            # Return a default tracking response for unknown waybills
            return TrackingResponse(
                success=True,
                waybill_number=waybill_number,
                tracking_number=waybill_number,
                status=UnifiedStatus.IN_TRANSIT.value,
                status_description="Package is in transit",
                last_updated=datetime.now(),
                events=[
                    TrackingEvent(
                        timestamp=datetime.now() - timedelta(hours=2),
                        status=UnifiedStatus.CREATED.value,
                        raw_status="CREATED",
                        description="Shipment created",
                        location="Riyadh",
                    ),
                    TrackingEvent(
                        timestamp=datetime.now() - timedelta(hours=1),
                        status=UnifiedStatus.PICKED_UP.value,
                        raw_status="PICKED_UP",
                        description="Package picked up by courier",
                        location="Riyadh Hub",
                    ),
                    TrackingEvent(
                        timestamp=datetime.now(),
                        status=UnifiedStatus.IN_TRANSIT.value,
                        raw_status="IN_TRANSIT",
                        description="Package in transit to destination",
                        location="In Transit",
                    ),
                ],
            )

        # Use stored data
        events = [
            TrackingEvent(
                timestamp=evt["timestamp"],
                status=evt["status"],
                raw_status=evt["status"],
                description=evt["description"],
                location=evt.get("location", ""),
            )
            for evt in shipment_data["events"]
        ]

        return TrackingResponse(
            success=True,
            waybill_number=waybill_number,
            tracking_number=waybill_number,
            status=shipment_data["status"],
            status_description=f"Current status: {shipment_data['status']}",
            last_updated=datetime.now(),
            events=events,
        )

    def cancel_shipment(self, waybill_number: str, reason: str = "") -> CancelResponse:
        """Cancel a mock shipment."""
        if waybill_number in self._shipments:
            self._shipments[waybill_number]["status"] = UnifiedStatus.CANCELLED.value
            self._shipments[waybill_number]["events"].append({
                "timestamp": datetime.now(),
                "status": UnifiedStatus.CANCELLED.value,
                "description": f"Shipment cancelled. Reason: {reason or 'No reason provided'}",
                "location": "",
            })

        return CancelResponse(
            success=True,
            waybill_number=waybill_number,
            cancellation_id=f"CANCEL-{uuid.uuid4().hex[:8].upper()}",
            refund_amount=25.0,
            currency="SAR",
        )

    def print_label(self, waybill_number: str) -> LabelResponse:
        """Get mock label."""
        return LabelResponse(
            success=True,
            waybill_number=waybill_number,
            label_url=f"https://mock-courier.example.com/labels/{waybill_number}.pdf",
            label_data="JVBERi0xLjQKMSAwIG9iago8PC9UeXBlL1BhZ2VzL0tpZHNbXC9Db3VudCAwPj4KZW5kb2Jq",
            format="PDF",
        )
