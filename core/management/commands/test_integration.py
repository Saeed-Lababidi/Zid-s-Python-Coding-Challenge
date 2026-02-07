"""
Management command to run integration tests.
"""
from django.core.management.base import BaseCommand
from core.services import ShipmentService
from core.couriers.factory import CourierFactory
import json

class Command(BaseCommand):
    help = 'Runs initialization and integration tests for the ZidShip Courier Framework'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Integration Tests...'))

        # 1. Test Courier Factory
        self.stdout.write('Testing Courier Factory...')
        providers = CourierFactory.get_available_providers()
        self.stdout.write(f'Available Providers: {providers}')
        
        # 2. Create Shipment (MOCK)
        self.stdout.write('\nTesting Create Shipment (MOCK)...')
        payload = {
            "reference_number": "INT-TEST-001",
            "sender": {
                "name": "Integration Sender",
                "address_line1": "Test Street",
                "city": "Riyadh",
                "country": "SA",
                "phone": "123456789"
            },
            "recipient": {
                "name": "Integration Recipient",
                "address_line1": "Test Ave",
                "city": "Jeddah",
                "country": "SA",
                "phone": "987654321"
            },
            "package": {
                "weight": 2.5,
                "description": "Integration Test Package",
                "length": 10,
                "width": 10,
                "height": 10
            },
            "priority": "STANDARD"
        }
        
        try:
            # Use MOCK provider explicitly
            result = ShipmentService.create_shipment(payload, courier_provider="MOCK")
            waybill = result['waybill_number']
            self.stdout.write(self.style.SUCCESS(f'Shipment Created! Waybill: {waybill}'))
            
            # 3. Track Shipment
            self.stdout.write('\nTesting Track Shipment...')
            track_result = ShipmentService.track_shipment(waybill)
            self.stdout.write(f"Status: {track_result['status']}")
            self.stdout.write(f"Events: {len(track_result['events'])}")
            self.stdout.write(self.style.SUCCESS('Tracking Successful!'))

            # 4. Print Label
            self.stdout.write('\nTesting Print Label...')
            label_result = ShipmentService.print_label(waybill)
            self.stdout.write(f"Label URL: {label_result['label_url']}")
            self.stdout.write(self.style.SUCCESS('Label Retrieved!'))
            
            # 5. Cancel Shipment
            self.stdout.write('\nTesting Cancel Shipment...')
            cancel_result = ShipmentService.cancel_shipment(waybill, reason="Integration Test End")
            self.stdout.write(f"Refund Amount: {cancel_result['refund_amount']} {cancel_result['currency']}")
            self.stdout.write(self.style.SUCCESS('Cancellation Successful!'))
            
            self.stdout.write(self.style.SUCCESS('\nAll Integration Tests Passed!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nIntegration Test Failed: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
