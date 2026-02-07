"""
Serializers for API request/response validation.
"""
from rest_framework import serializers


class AddressSerializer(serializers.Serializer):
    """Address serializer for sender/recipient."""
    name = serializers.CharField(max_length=200)
    address_line1 = serializers.CharField(max_length=500)
    address_line2 = serializers.CharField(max_length=500, required=False, allow_blank=True)
    city = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    country = serializers.CharField(max_length=2, help_text="ISO 3166-1 alpha-2 country code")
    phone = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True)


class PackageSerializer(serializers.Serializer):
    """Package details serializer."""
    weight = serializers.FloatField(min_value=0.01)
    description = serializers.CharField(max_length=500)
    length = serializers.FloatField(min_value=0, required=False, default=0)
    width = serializers.FloatField(min_value=0, required=False, default=0)
    height = serializers.FloatField(min_value=0, required=False, default=0)
    value = serializers.FloatField(min_value=0, required=False, default=0)


class CreateShipmentSerializer(serializers.Serializer):
    """Serializer for creating a shipment."""
    reference_number = serializers.CharField(max_length=100)
    sender = AddressSerializer()
    recipient = AddressSerializer()
    package = PackageSerializer()
    courier_provider = serializers.CharField(max_length=50, required=False, allow_blank=True)
    priority = serializers.ChoiceField(
        choices=["STANDARD", "EXPRESS", "PRIORITY"],
        default="STANDARD",
        required=False,
    )
    cod_amount = serializers.FloatField(min_value=0, required=False, default=0)
    cod_currency = serializers.CharField(max_length=3, required=False, default="SAR")
    insurance_amount = serializers.FloatField(min_value=0, required=False, default=0)
    special_instructions = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class ShipmentResponseSerializer(serializers.Serializer):
    """Serializer for shipment response."""
    success = serializers.BooleanField()
    waybill_number = serializers.CharField()
    tracking_number = serializers.CharField()
    courier_provider = serializers.CharField()
    status = serializers.CharField()
    estimated_delivery_date = serializers.DateTimeField(allow_null=True)
    label_url = serializers.CharField(allow_blank=True)


class TrackingEventSerializer(serializers.Serializer):
    """Serializer for tracking events."""
    timestamp = serializers.CharField()
    status = serializers.CharField()
    description = serializers.CharField()
    location = serializers.CharField(allow_blank=True)


class TrackingResponseSerializer(serializers.Serializer):
    """Serializer for tracking response."""
    success = serializers.BooleanField()
    waybill_number = serializers.CharField()
    status = serializers.CharField()
    status_description = serializers.CharField()
    last_updated = serializers.CharField()
    events = TrackingEventSerializer(many=True)


class CancelShipmentSerializer(serializers.Serializer):
    """Serializer for cancellation request."""
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class CancelResponseSerializer(serializers.Serializer):
    """Serializer for cancellation response."""
    success = serializers.BooleanField()
    waybill_number = serializers.CharField()
    cancellation_id = serializers.CharField(allow_blank=True)
    refund_amount = serializers.FloatField()
    currency = serializers.CharField()
    errors = serializers.ListSerializer(child=serializers.CharField(), required=False)


class LabelResponseSerializer(serializers.Serializer):
    """Serializer for label response."""
    success = serializers.BooleanField()
    waybill_number = serializers.CharField()
    label_url = serializers.CharField(allow_blank=True)
    label_data = serializers.CharField(allow_blank=True)
    errors = serializers.ListSerializer(child=serializers.CharField(), required=False)


class ShipmentDetailSerializer(serializers.Serializer):
    """Serializer for shipment details."""
    id = serializers.CharField()
    reference_number = serializers.CharField()
    waybill_number = serializers.CharField()
    tracking_number = serializers.CharField()
    courier_provider = serializers.CharField()
    status = serializers.CharField()
    priority = serializers.CharField()
    sender = serializers.DictField()
    recipient = serializers.DictField()
    package = serializers.DictField()
    service_type = serializers.CharField()
    cod_amount = serializers.FloatField()
    cost = serializers.FloatField()
    currency = serializers.CharField()
    label_url = serializers.CharField(allow_blank=True)
    estimated_delivery_date = serializers.CharField(allow_null=True)
    created_at = serializers.CharField()
    updated_at = serializers.CharField()


class CourierInfoSerializer(serializers.Serializer):
    """Serializer for courier information."""
    provider = serializers.CharField()
    features = serializers.ListSerializer(child=serializers.CharField())


class HealthSerializer(serializers.Serializer):
    """Serializer for health check response."""
    status = serializers.CharField()
    timestamp = serializers.CharField()
    version = serializers.CharField()
