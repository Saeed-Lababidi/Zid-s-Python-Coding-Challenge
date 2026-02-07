"""
API Views for shipment management.
"""
import logging
from datetime import datetime

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .services import ShipmentService
from .couriers.factory import CourierFactory
from .serializers import (
    CreateShipmentSerializer,
    ShipmentResponseSerializer,
    TrackingResponseSerializer,
    CancelShipmentSerializer,
    CancelResponseSerializer,
    LabelResponseSerializer,
    ShipmentDetailSerializer,
    CourierInfoSerializer,
    HealthSerializer,
)


logger = logging.getLogger(__name__)


# --- Health Endpoints ---

@extend_schema(
    tags=["Health"],
    summary="Health Check",
    description="Basic health check endpoint",
    responses={200: HealthSerializer},
)
@api_view(["GET"])
def health_check(request):
    """Basic health check."""
    return Response({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    })


# --- Courier Endpoints ---

@extend_schema(
    tags=["Couriers"],
    summary="List Available Couriers",
    description="Get list of all available courier providers",
    responses={200: CourierInfoSerializer(many=True)},
)
@api_view(["GET"])
def list_couriers(request):
    """List all available courier providers."""
    providers = CourierFactory.get_available_providers()
    result = []
    for provider in providers:
        try:
            courier = CourierFactory.get_courier(provider)
            result.append({
                "provider": provider,
                "features": courier.get_supported_features(),
            })
        except Exception as e:
            logger.warning(f"Could not get info for {provider}: {e}")
            result.append({
                "provider": provider,
                "features": [],
            })
    return Response(result)


@extend_schema(
    tags=["Couriers"],
    summary="Get Courier Details",
    description="Get details for a specific courier provider",
    responses={200: CourierInfoSerializer},
)
@api_view(["GET"])
def get_courier(request, provider):
    """Get details for a specific courier."""
    try:
        courier = CourierFactory.get_courier(provider)
        return Response({
            "provider": courier.get_provider_name(),
            "features": courier.get_supported_features(),
        })
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


# --- Shipment Endpoints ---

@extend_schema(
    tags=["Shipments"],
    summary="Create Shipment",
    description="Create a new shipment with the specified courier",
    request=CreateShipmentSerializer,
    responses={201: ShipmentResponseSerializer},
)
@api_view(["POST"])
def create_shipment(request):
    """Create a new shipment."""
    serializer = CreateShipmentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        data = serializer.validated_data
        courier_provider = data.pop("courier_provider", None)
        result = ShipmentService.create_shipment(data, courier_provider or None)
        return Response(result, status=status.HTTP_201_CREATED)
    except ValueError as e:
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        logger.exception("Failed to create shipment")
        return Response(
            {"success": False, "error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@extend_schema(
    tags=["Shipments"],
    summary="Get Shipment Details",
    description="Get details of a shipment by waybill number",
    responses={200: ShipmentDetailSerializer},
)
@api_view(["GET"])
def get_shipment(request, waybill_number):
    """Get shipment details."""
    try:
        result = ShipmentService.get_shipment(waybill_number)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    tags=["Shipments"],
    summary="Track Shipment",
    description="Get real-time tracking information for a shipment",
    responses={200: TrackingResponseSerializer},
)
@api_view(["GET"])
def track_shipment(request, waybill_number):
    """Track a shipment."""
    try:
        result = ShipmentService.track_shipment(waybill_number)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    tags=["Shipments"],
    summary="Cancel Shipment",
    description="Cancel a shipment",
    request=CancelShipmentSerializer,
    responses={200: CancelResponseSerializer},
)
@api_view(["DELETE"])
def cancel_shipment(request, waybill_number):
    """Cancel a shipment."""
    serializer = CancelShipmentSerializer(data=request.data or {})
    serializer.is_valid(raise_exception=True)

    try:
        reason = serializer.validated_data.get("reason", "")
        result = ShipmentService.cancel_shipment(waybill_number, reason)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    tags=["Shipments"],
    summary="Print Label",
    description="Get or generate shipping label for a shipment",
    responses={200: LabelResponseSerializer},
)
@api_view(["GET"])
def print_label(request, waybill_number):
    """Get shipping label."""
    try:
        result = ShipmentService.print_label(waybill_number)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
