"""
Courier Factory - Registry pattern for courier instantiation.
"""
import logging
from typing import Dict, Any, Type, Optional

from .base import CourierBase
from .smsa import SMSACourier
from .mock import MockCourier
from ..enums import CourierProvider


logger = logging.getLogger(__name__)


class CourierFactory:
    """
    Factory class for creating courier instances.
    Uses registry pattern - couriers register themselves.
    """

    _registry: Dict[str, Type[CourierBase]] = {
        CourierProvider.SMSA.value: SMSACourier,
        CourierProvider.MOCK.value: MockCourier,
    }

    _instances: Dict[str, CourierBase] = {}

    @classmethod
    def register(cls, provider: str, courier_class: Type[CourierBase]) -> None:
        """Register a new courier class."""
        cls._registry[provider.upper()] = courier_class
        logger.info(f"Registered courier: {provider}")

    @classmethod
    def get_courier(cls, provider: str, config: Optional[Dict[str, Any]] = None) -> CourierBase:
        """
        Get a courier instance by provider name.
        Instances are cached for reuse.

        Args:
            provider: Courier provider name (e.g., 'SMSA', 'MOCK')
            config: Configuration dictionary for the courier

        Returns:
            CourierBase instance

        Raises:
            ValueError: If provider is not registered
        """
        provider_upper = provider.upper()

        # Return cached instance if available and no new config provided
        if provider_upper in cls._instances and config is None:
            return cls._instances[provider_upper]

        if provider_upper not in cls._registry:
            available = list(cls._registry.keys())
            raise ValueError(f"Unknown courier provider: {provider}. Available: {available}")

        courier_class = cls._registry[provider_upper]
        config = config or cls._get_default_config(provider_upper)

        instance = courier_class(config)
        cls._instances[provider_upper] = instance

        logger.info(f"Created courier instance: {provider}")
        return instance

    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available courier providers."""
        return list(cls._registry.keys())

    @classmethod
    def _get_default_config(cls, provider: str) -> Dict[str, Any]:
        """Get default configuration for a provider."""
        from django.conf import settings

        if provider == CourierProvider.SMSA.value:
            return {
                "api_key": getattr(settings, "SMSA_API_KEY", "mock-key"),
                "base_url": getattr(settings, "SMSA_BASE_URL", "https://api.smsa.com"),
                "mock_mode": getattr(settings, "SMSA_MOCK_MODE", True),
            }
        elif provider == CourierProvider.MOCK.value:
            return {
                "api_key": "mock-key",
                "base_url": "https://mock.example.com",
                "mock_mode": True,
            }

        return {"api_key": "default", "base_url": "https://api.example.com", "mock_mode": True}

    @classmethod
    def get_best_courier(
        cls,
        origin: str,
        destination: str,
        weight: float,
        priority: str = "STANDARD",
    ) -> str:
        """
        Determine the best courier for a shipment based on criteria.

        Args:
            origin: Origin country code
            destination: Destination country code
            weight: Package weight in kg
            priority: Shipment priority

        Returns:
            Provider name string
        """
        # Simple logic - in production this would be more sophisticated
        # Saudi domestic -> SMSA
        if origin == "SA" and destination == "SA":
            if CourierProvider.SMSA.value in cls._registry:
                return CourierProvider.SMSA.value

        # Default to MOCK for testing
        if CourierProvider.MOCK.value in cls._registry:
            return CourierProvider.MOCK.value

        # Fallback to first available
        available = cls.get_available_providers()
        if available:
            return available[0]

        raise ValueError("No courier providers available")

    @classmethod
    def supports_feature(cls, provider: str, feature: str) -> bool:
        """Check if a provider supports a specific feature."""
        try:
            courier = cls.get_courier(provider)
            return courier.supports_feature(feature)
        except (ValueError, Exception):
            return False
