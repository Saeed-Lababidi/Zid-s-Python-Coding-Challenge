"""
Unit and Integration tests for ZidShip Courier Framework.
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from datetime import datetime

from .models import Shipment, TrackingEvent
from .enums import UnifiedStatus, CourierProvider
from .couriers.factory import CourierFactory
from .couriers.mock import MockCourier
from .dtos import ShipmentRequest, Address, PackageDetails


class CourierFactoryTests(TestCase):
    def test_get_courier_valid(self):
        courier = CourierFactory.get_courier("SMSA")
        self.assertEqual(courier.get_provider_name(), "SMSA")

    def test_get_courier_invalid(self):
        with self.assertRaises(ValueError):
            CourierFactory.get_courier("INVALID")

    def test_get_best_courier_saudi(self):
        provider = CourierFactory.get_best_courier("SA", "SA", 5.0)
        self.assertEqual(provider, "SMSA")

    def test_get_best_courier_mock_fallback(self):
        # Should fallback to Mock or available
        provider = CourierFactory.get_best_courier("US", "UK", 5.0)
        self.assertIn(provider, ["MOCK", "SMSA"])


class MockCourierTests(TestCase):
    def setUp(self):
        self.courier = MockCourier({"mock": True})
        self.request = ShipmentRequest(
            reference_number="REF123",
            sender=Address(
                name="Sender", address_line1="Line 1", city="Riyadh", country="SA", phone="123"
            ),
            recipient=Address(
                name="Recipient", address_line1="Line 1", city="Jeddah", country="SA", phone="456"
            ),
            package=PackageDetails(weight=10.0, description="Test Package"),
        )

    def test_create_shipment(self):
        response = self.courier.create_shipment(self.request)
        self.assertTrue(response.success)
        self.assertIsNotNone(response.waybill_number)
        self.assertIn("MOCK", response.waybill_number)

    def test_track_shipment_new(self):
        # Create first
        create_res = self.courier.create_shipment(self.request)
        
        # Track
        track_res = self.courier.track_shipment(create_res.waybill_number)
        self.assertTrue(track_res.success)
        self.assertEqual(track_res.status, UnifiedStatus.CREATED.value)


class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_payload = {
            "reference_number": "ORDER-001",
            "courier_provider": "MOCK",  # Force Mock provider for tests
            "sender": {
                "name": "Zid Store",
                "address_line1": "Riyadh Business Park",
                "city": "Riyadh",
                "country": "SA",
                "phone": "+966500000000"
            },
            "recipient": {
                "name": "Customer",
                "address_line1": "King Road",
                "city": "Jeddah",
                "country": "SA",
                "phone": "+966511111111"
            },
            "package": {
                "weight": 5.0,
                "description": "Electronics",
                "length": 10,
                "width": 10,
                "height": 10
            },
            "priority": "EXPRESS"
        }

    def test_health_check(self):
        response = self.client.get("/health/") # This path might be wrong relative to core urls
        # Note: urls are under /api/v1/ in main urls.py
        response = self.client.get("/api/v1/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "healthy")

    def test_create_shipment_api(self):
        response = self.client.post(
            "/api/v1/shipments/",
            self.valid_payload,
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertIsNotNone(response.data["waybill_number"])
        
        # Verify DB
        shipment = Shipment.objects.get(waybill_number=response.data["waybill_number"])
        self.assertEqual(shipment.reference_number, "ORDER-001")
        self.assertEqual(shipment.status, UnifiedStatus.CREATED.value)

    def test_track_shipment_api(self):
        # Create first
        create_res = self.client.post(
            "/api/v1/shipments/",
            self.valid_payload,
            format="json"
        )
        waybill = create_res.data["waybill_number"]

        # Track
        response = self.client.get(f"/api/v1/shipments/{waybill}/track/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    def test_cancel_shipment_api(self):
        # Create first
        create_res = self.client.post(
            "/api/v1/shipments/",
            self.valid_payload,
            format="json"
        )
        waybill = create_res.data["waybill_number"]

        # Cancel
        response = self.client.delete(
            f"/api/v1/shipments/{waybill}/cancel/",
            {"reason": "Customer request"},
            format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        
        # Verify DB status
        shipment = Shipment.objects.get(waybill_number=waybill)
        # Verify via tracking because cancel is async in some flows, but sync here
        self.assertEqual(shipment.status, UnifiedStatus.CANCELLED.value)

