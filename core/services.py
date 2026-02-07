"""
Shipment Service - Business logic layer.
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from django.db import transaction

from .models import Shipment, TrackingEvent
from .enums import UnifiedStatus, CourierProvider
from .couriers.factory import CourierFactory
from .dtos import (
    ShipmentRequest,
    ShipmentResponse,
    TrackingResponse as TrackingResponseDTO,
    CancelResponse as CancelResponseDTO,
    LabelResponse as LabelResponseDTO,
    Address,
    PackageDetails,
)


logger = logging.getLogger(__name__)


class ShipmentService:
    """
    Service class handling all shipment business logic.
    """

    @staticmethod
    @transaction.atomic
    def create_shipment(
        data: Dict[str, Any],
        courier_provider: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new shipment.

        Args:
            data: Shipment data dictionary
            courier_provider: Optional specific courier provider

        Returns:
            Dictionary with shipment details
        """
        # Build DTOs from data
        sender = Address(
            name=data["sender"]["name"],
            address_line1=data["sender"]["address_line1"],
            city=data["sender"]["city"],
            country=data["sender"]["country"],
            phone=data["sender"]["phone"],
            postal_code=data["sender"].get("postal_code", ""),
            address_line2=data["sender"].get("address_line2", ""),
            email=data["sender"].get("email", ""),
        )

        recipient = Address(
            name=data["recipient"]["name"],
            address_line1=data["recipient"]["address_line1"],
            city=data["recipient"]["city"],
            country=data["recipient"]["country"],
            phone=data["recipient"]["phone"],
            postal_code=data["recipient"].get("postal_code", ""),
            address_line2=data["recipient"].get("address_line2", ""),
            email=data["recipient"].get("email", ""),
        )

        package = PackageDetails(
            weight=data["package"]["weight"],
            description=data["package"]["description"],
            length=data["package"].get("length", 0),
            width=data["package"].get("width", 0),
            height=data["package"].get("height", 0),
            value=data["package"].get("value", 0),
        )

        request = ShipmentRequest(
            reference_number=data["reference_number"],
            sender=sender,
            recipient=recipient,
            package=package,
            priority=data.get("priority", "STANDARD"),
            cod_amount=data.get("cod_amount", 0),
            special_instructions=data.get("special_instructions", ""),
        )

        # Determine courier
        if courier_provider:
            if courier_provider.upper() not in CourierFactory.get_available_providers():
                raise ValueError(f"Unknown courier: {courier_provider}")
            provider = courier_provider.upper()
        else:
            provider = CourierFactory.get_best_courier(
                origin=sender.country,
                destination=recipient.country,
                weight=package.weight,
                priority=request.priority,
            )

        logger.info(f"Creating shipment with {provider} for ref: {request.reference_number}")

        # Get courier and create shipment
        courier = CourierFactory.get_courier(provider)
        response: ShipmentResponse = courier.create_shipment(request)

        if not response.success:
            raise ValueError(f"Courier error: {'; '.join(response.errors)}")

        # Save to database
        shipment = Shipment.objects.create(
            reference_number=request.reference_number,
            waybill_number=response.waybill_number,
            tracking_number=response.tracking_number,
            courier_provider=provider,
            status=UnifiedStatus.CREATED.value,
            priority=request.priority,
            sender_data=sender.to_dict(),
            recipient_data=recipient.to_dict(),
            package_data=package.to_dict(),
            courier_specific_data=response.courier_data,
            service_type=response.service_type,
            special_instructions=request.special_instructions,
            cod_amount=request.cod_amount,
            cod_currency=request.cod_currency,
            estimated_delivery_date=response.estimated_delivery_date,
            cost=response.cost,
            currency=response.currency,
            label_url=response.label_url,
            label_data=response.label_data,
        )

        # Create initial tracking event
        TrackingEvent.objects.create(
            shipment=shipment,
            status=UnifiedStatus.CREATED.value,
            raw_status="CREATED",
            description="Shipment created successfully",
            location=sender.city,
            timestamp=datetime.now(),
        )

        logger.info(f"Shipment saved: {shipment.waybill_number}")

        return {
            "success": True,
            "waybill_number": shipment.waybill_number,
            "tracking_number": shipment.tracking_number,
            "courier_provider": provider,
            "status": shipment.status,
            "estimated_delivery_date": shipment.estimated_delivery_date,
            "label_url": shipment.label_url,
        }

    @staticmethod
    def track_shipment(waybill_number: str) -> Dict[str, Any]:
        """
        Track a shipment by waybill number.
        """
        try:
            shipment = Shipment.objects.get(waybill_number=waybill_number)
        except Shipment.DoesNotExist:
            raise ValueError(f"Shipment not found: {waybill_number}")

        courier = CourierFactory.get_courier(shipment.courier_provider)
        response: TrackingResponseDTO = courier.track_shipment(waybill_number)

        # Update shipment status
        if response.success:
            shipment.status = response.status
            shipment.last_status_description = response.status_description
            shipment.save()

            # Save new tracking events
            for event in response.events:
                TrackingEvent.objects.get_or_create(
                    shipment=shipment,
                    timestamp=event.timestamp,
                    status=event.status,
                    defaults={
                        "raw_status": event.raw_status,
                        "description": event.description,
                        "location": event.location,
                    },
                )

        # Get all events from DB
        events = shipment.tracking_events.all().order_by("timestamp")

        return {
            "success": response.success,
            "waybill_number": waybill_number,
            "status": response.status,
            "status_description": response.status_description,
            "last_updated": response.last_updated.isoformat(),
            "events": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "status": e.status,
                    "description": e.description,
                    "location": e.location,
                }
                for e in events
            ],
        }

    @staticmethod
    def cancel_shipment(waybill_number: str, reason: str = "") -> Dict[str, Any]:
        """
        Cancel a shipment.
        """
        try:
            shipment = Shipment.objects.get(waybill_number=waybill_number)
        except Shipment.DoesNotExist:
            raise ValueError(f"Shipment not found: {waybill_number}")

        if not CourierFactory.supports_feature(shipment.courier_provider, "cancellation"):
            raise ValueError(f"Cancellation not supported by {shipment.courier_provider}")

        courier = CourierFactory.get_courier(shipment.courier_provider)
        response: CancelResponseDTO = courier.cancel_shipment(waybill_number, reason)

        if response.success:
            shipment.status = UnifiedStatus.CANCELLED.value
            shipment.last_status_description = f"Cancelled: {reason}"
            shipment.save()

            TrackingEvent.objects.create(
                shipment=shipment,
                status=UnifiedStatus.CANCELLED.value,
                raw_status="CANCELLED",
                description=f"Shipment cancelled. Reason: {reason or 'N/A'}",
                timestamp=datetime.now(),
            )

        return {
            "success": response.success,
            "waybill_number": waybill_number,
            "cancellation_id": response.cancellation_id,
            "refund_amount": response.refund_amount,
            "currency": response.currency,
            "errors": response.errors,
        }

    @staticmethod
    def get_shipment(waybill_number: str) -> Dict[str, Any]:
        """
        Get shipment details.
        """
        try:
            shipment = Shipment.objects.get(waybill_number=waybill_number)
        except Shipment.DoesNotExist:
            raise ValueError(f"Shipment not found: {waybill_number}")

        return {
            "id": str(shipment.id),
            "reference_number": shipment.reference_number,
            "waybill_number": shipment.waybill_number,
            "tracking_number": shipment.tracking_number,
            "courier_provider": shipment.courier_provider,
            "status": shipment.status,
            "priority": shipment.priority,
            "sender": shipment.sender_data,
            "recipient": shipment.recipient_data,
            "package": shipment.package_data,
            "service_type": shipment.service_type,
            "cod_amount": float(shipment.cod_amount),
            "cost": float(shipment.cost),
            "currency": shipment.currency,
            "label_url": shipment.label_url,
            "estimated_delivery_date": shipment.estimated_delivery_date.isoformat() if shipment.estimated_delivery_date else None,
            "created_at": shipment.created_at.isoformat(),
            "updated_at": shipment.updated_at.isoformat(),
        }

    @staticmethod
    def print_label(waybill_number: str) -> Dict[str, Any]:
        """
        Get or generate shipping label.
        """
        try:
            shipment = Shipment.objects.get(waybill_number=waybill_number)
        except Shipment.DoesNotExist:
            raise ValueError(f"Shipment not found: {waybill_number}")

        # Return cached label if available
        if shipment.label_url:
            return {
                "success": True,
                "waybill_number": waybill_number,
                "label_url": shipment.label_url,
                "label_data": shipment.label_data,
            }

        # Try to fetch from courier
        courier = CourierFactory.get_courier(shipment.courier_provider)
        response: LabelResponseDTO = courier.print_label(waybill_number)

        if response.success and response.label_url:
            shipment.label_url = response.label_url
            shipment.label_data = response.label_data
            shipment.save()

        return {
            "success": response.success,
            "waybill_number": waybill_number,
            "label_url": response.label_url,
            "label_data": response.label_data,
            "errors": response.errors,
        }
