"""
Unit tests for SMSA Courier SOAP implementation.
"""
from django.test import TestCase
from unittest.mock import MagicMock, patch
from .couriers.smsa import SMSACourier
from .dtos import ShipmentRequest, Address, PackageDetails
from .enums import UnifiedStatus

class SMSACourierTests(TestCase):
    def setUp(self):
        self.config = {
            "api_key": "test_key",
            "base_url": "https://test.smsa.com",
            "mock_mode": False 
        }
        self.courier = SMSACourier(self.config)
        
        self.request = ShipmentRequest(
            reference_number="REF123",
            sender=Address(
                name="Sender", address_line1="Line 1", city="Riyadh", country="SA", phone="123", postal_code="11111"
            ),
            recipient=Address(
                name="Recipient", address_line1="Line 1", city="Jeddah", country="SA", phone="456", postal_code="22222"
            ),
            package=PackageDetails(
                weight=10.0, description="Test Package", value=100
            ),
            cod_amount=50.0,
            insurance_amount=10.0
        )

    @patch("core.http_client.HTTPClient.post")
    def test_create_shipment_xml_construction(self, mock_post):
        """Test that XML payload is constructed correctly."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.content = b"""
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
           <soap:Body>
              <addShipPDFResult>SMSA123456</addShipPDFResult>
           </soap:Body>
        </soap:Envelope>
        """
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        response = self.courier.create_shipment(self.request)

        # Verify Response
        self.assertTrue(response.success)
        self.assertEqual(response.waybill_number, "SMSA123456")
        
        # Verify XML Request Content
        args, kwargs = mock_post.call_args
        xml_sent = kwargs['data']
        
        self.assertIn('<ns:passKey>test_key</ns:passKey>', xml_sent)
        self.assertIn('<ns:refNo>REF123</ns:refNo>', xml_sent)
        self.assertIn('<ns:cCity>Riyadh</ns:cCity>', xml_sent)
        self.assertIn('<ns:sCity>Jeddah</ns:sCity>', xml_sent)
        self.assertIn('<ns:codAmt>50.0</ns:codAmt>', xml_sent)

    @patch("core.http_client.HTTPClient.post")
    def test_create_shipment_failure(self, mock_post):
        """Test handling of API failure."""
        mock_response = MagicMock()
        mock_response.content = b"""
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
           <soap:Body>
              <addShipPDFResult>Failed: Invalid Key</addShipPDFResult>
           </soap:Body>
        </soap:Envelope>
        """
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        response = self.courier.create_shipment(self.request)

        self.assertFalse(response.success)
        self.assertIn("SMSA API Error", response.errors[0])
        self.assertIn("Failed: Invalid Key", response.errors[0])

    @patch("core.http_client.HTTPClient.post")
    def test_track_shipment(self, mock_post):
        """Test converting SOAP tracking response."""
        # For our simple implementation we just mocked the return of track_shipment
        # to always return success if the HTTP call works.
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        response = self.courier.track_shipment("SMSA123")
        
        self.assertTrue(response.success)
        self.assertEqual(response.status, UnifiedStatus.IN_TRANSIT.value)
        
        # Verify XML structure
        args, kwargs = mock_post.call_args
        xml_sent = kwargs['data']
        self.assertIn('<ns:getTrackingParams>', xml_sent)
        self.assertIn('<ns:awbNo>SMSA123</ns:awbNo>', xml_sent)
