"""
Abstract Base Class for all courier implementations.
Defines the contract that all couriers must implement.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

from ..dtos import (
    ShipmentRequest,
    ShipmentResponse,
    TrackingResponse,
    CancelResponse,
    LabelResponse,
)
from ..enums import UnifiedStatus


logger = logging.getLogger(__name__)


class CourierBase(ABC):
    """
    Abstract base courier class.
    All courier implementations must extend this class.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the courier with configuration.

        Args:
            config: Dictionary containing API keys, URLs, etc.
        """
        self.config = config
        self.is_initialized = False
        self._validate_config(config)
        self.is_initialized = True
        logger.info(f"Courier {self.get_provider_name()} initialized successfully")

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate the configuration. Override for courier-specific validation."""
        if not config.get("api_key"):
            raise ValueError("API key is required")
        if not config.get("base_url"):
            raise ValueError("Base URL is required")

    def _ensure_initialized(self) -> None:
        """Ensure the courier is initialized before operations."""
        if not self.is_initialized:
            raise RuntimeError("Courier not initialized. Call initialize() first.")

    # --- Abstract Methods ---

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'SMSA', 'ARAMEX')."""
        pass

    @abstractmethod
    def get_supported_features(self) -> List[str]:
        """Return list of supported features (e.g., ['cancellation', 'cod', 'insurance'])."""
        pass

    @abstractmethod
    def map_status(self, raw_status: str) -> UnifiedStatus:
        """Map courier-specific status to unified status."""
        pass

    @abstractmethod
    def create_shipment(self, request: ShipmentRequest) -> ShipmentResponse:
        """Create a new shipment."""
        pass

    @abstractmethod
    def track_shipment(self, waybill_number: str) -> TrackingResponse:
        """Track a shipment by waybill number."""
        pass

    @abstractmethod
    def cancel_shipment(self, waybill_number: str, reason: str = "") -> CancelResponse:
        """Cancel a shipment."""
        pass

    @abstractmethod
    def print_label(self, waybill_number: str) -> LabelResponse:
        """Get or generate shipping label."""
        pass

    # --- Common Methods ---

    def supports_feature(self, feature: str) -> bool:
        """Check if this courier supports a specific feature."""
        return feature in self.get_supported_features()

    def validate_shipment_request(self, request: ShipmentRequest) -> List[str]:
        """
        Validate a shipment request. Returns list of error messages.
        Override for courier-specific validation.
        """
        errors = []

        if not request.reference_number:
            errors.append("Reference number is required")

        if not request.sender.name:
            errors.append("Sender name is required")
        if not request.sender.address_line1:
            errors.append("Sender address is required")
        if not request.sender.city:
            errors.append("Sender city is required")
        if not request.sender.country:
            errors.append("Sender country is required")
        if not request.sender.phone:
            errors.append("Sender phone is required")

        if not request.recipient.name:
            errors.append("Recipient name is required")
        if not request.recipient.address_line1:
            errors.append("Recipient address is required")
        if not request.recipient.city:
            errors.append("Recipient city is required")
        if not request.recipient.country:
            errors.append("Recipient country is required")
        if not request.recipient.phone:
            errors.append("Recipient phone is required")

        if not request.package.weight or request.package.weight <= 0:
            errors.append("Package weight must be greater than 0")
        if not request.package.description:
            errors.append("Package description is required")

        return errors
