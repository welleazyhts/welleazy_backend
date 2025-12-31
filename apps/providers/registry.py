"""
Provider Registry - Factory pattern for healthcare service providers.

Manages registration and instantiation of providers for:
- Consultation (Apollo, etc.)
- Diagnostics (Apollo, Thyrocare, Healthians, Dr. Lal, RedCliff, SRL, Orange Health)
- Pharmacy (Tata 1MG, Apollo Pharmacy)
"""

from typing import Dict, Type, Optional, List, Any
from django.conf import settings

from .base.consultation import ConsultationProvider
from .base.diagnostics import DiagnosticsProvider
from .base.pharmacy import PharmacyProvider
from .base.exceptions import ProviderNotFoundError, ProviderNotConfiguredError


class ProviderRegistry:
    """
    Central registry for all healthcare service providers.

    Usage:
        # Register a provider
        registry.register_consultation('apollo', ApolloConsultationProvider)

        # Get a provider instance
        provider = registry.get_consultation_provider('apollo')

        # Get default provider
        provider = registry.get_default_consultation_provider()
    """

    def __init__(self):
        # Provider class registries
        self._consultation_providers: Dict[str, Type[ConsultationProvider]] = {}
        self._diagnostics_providers: Dict[str, Type[DiagnosticsProvider]] = {}
        self._pharmacy_providers: Dict[str, Type[PharmacyProvider]] = {}

        # Provider instance cache (singleton per provider)
        self._consultation_instances: Dict[str, ConsultationProvider] = {}
        self._diagnostics_instances: Dict[str, DiagnosticsProvider] = {}
        self._pharmacy_instances: Dict[str, PharmacyProvider] = {}

    # ==================== Registration Methods ====================

    def register_consultation(
        self,
        name: str,
        provider_class: Type[ConsultationProvider]
    ) -> None:
        """Register a consultation provider."""
        self._consultation_providers[name.lower()] = provider_class

    def register_diagnostics(
        self,
        name: str,
        provider_class: Type[DiagnosticsProvider]
    ) -> None:
        """Register a diagnostics provider."""
        self._diagnostics_providers[name.lower()] = provider_class

    def register_pharmacy(
        self,
        name: str,
        provider_class: Type[PharmacyProvider]
    ) -> None:
        """Register a pharmacy provider."""
        self._pharmacy_providers[name.lower()] = provider_class

    # ==================== Provider Retrieval ====================

    def get_consultation_provider(
        self,
        name: str,
        config: Dict[str, Any] = None
    ) -> ConsultationProvider:
        """
        Get a consultation provider instance.

        Args:
            name: Provider name (e.g., 'apollo')
            config: Optional configuration override

        Returns:
            ConsultationProvider instance

        Raises:
            ProviderNotFoundError: If provider is not registered
        """
        name = name.lower()

        if name not in self._consultation_providers:
            raise ProviderNotFoundError(
                f"Consultation provider '{name}' not found. "
                f"Available: {list(self._consultation_providers.keys())}",
                provider=name
            )

        # Return cached instance if exists and no config override
        if name in self._consultation_instances and config is None:
            return self._consultation_instances[name]

        # Create new instance
        provider_class = self._consultation_providers[name]
        provider_config = config or self._get_provider_config('consultation', name)
        instance = provider_class(provider_config)

        # Cache if no config override
        if config is None:
            self._consultation_instances[name] = instance

        return instance

    def get_diagnostics_provider(
        self,
        name: str,
        config: Dict[str, Any] = None
    ) -> DiagnosticsProvider:
        """Get a diagnostics provider instance."""
        name = name.lower()

        if name not in self._diagnostics_providers:
            raise ProviderNotFoundError(
                f"Diagnostics provider '{name}' not found. "
                f"Available: {list(self._diagnostics_providers.keys())}",
                provider=name
            )

        if name in self._diagnostics_instances and config is None:
            return self._diagnostics_instances[name]

        provider_class = self._diagnostics_providers[name]
        provider_config = config or self._get_provider_config('diagnostics', name)
        instance = provider_class(provider_config)

        if config is None:
            self._diagnostics_instances[name] = instance

        return instance

    def get_pharmacy_provider(
        self,
        name: str,
        config: Dict[str, Any] = None
    ) -> PharmacyProvider:
        """Get a pharmacy provider instance."""
        name = name.lower()

        if name not in self._pharmacy_providers:
            raise ProviderNotFoundError(
                f"Pharmacy provider '{name}' not found. "
                f"Available: {list(self._pharmacy_providers.keys())}",
                provider=name
            )

        if name in self._pharmacy_instances and config is None:
            return self._pharmacy_instances[name]

        provider_class = self._pharmacy_providers[name]
        provider_config = config or self._get_provider_config('pharmacy', name)
        instance = provider_class(provider_config)

        if config is None:
            self._pharmacy_instances[name] = instance

        return instance

    # ==================== Default Providers ====================

    def get_default_consultation_provider(self) -> ConsultationProvider:
        """Get the default consultation provider."""
        default = getattr(settings, 'DEFAULT_CONSULTATION_PROVIDER', 'apollo')
        return self.get_consultation_provider(default)

    def get_default_diagnostics_provider(self) -> DiagnosticsProvider:
        """Get the default diagnostics provider."""
        default = getattr(settings, 'DEFAULT_DIAGNOSTICS_PROVIDER', 'apollo')
        return self.get_diagnostics_provider(default)

    def get_default_pharmacy_provider(self) -> PharmacyProvider:
        """Get the default pharmacy provider."""
        default = getattr(settings, 'DEFAULT_PHARMACY_PROVIDER', 'onemg')
        return self.get_pharmacy_provider(default)

    # ==================== Provider Listing ====================

    def list_consultation_providers(self) -> List[str]:
        """List all registered consultation providers."""
        return list(self._consultation_providers.keys())

    def list_diagnostics_providers(self) -> List[str]:
        """List all registered diagnostics providers."""
        return list(self._diagnostics_providers.keys())

    def list_pharmacy_providers(self) -> List[str]:
        """List all registered pharmacy providers."""
        return list(self._pharmacy_providers.keys())

    def get_all_providers_info(self) -> Dict[str, Any]:
        """Get information about all registered providers."""
        return {
            'consultation': self.list_consultation_providers(),
            'diagnostics': self.list_diagnostics_providers(),
            'pharmacy': self.list_pharmacy_providers(),
            'defaults': {
                'consultation': getattr(settings, 'DEFAULT_CONSULTATION_PROVIDER', 'apollo'),
                'diagnostics': getattr(settings, 'DEFAULT_DIAGNOSTICS_PROVIDER', 'apollo'),
                'pharmacy': getattr(settings, 'DEFAULT_PHARMACY_PROVIDER', 'onemg'),
            }
        }

    # ==================== Configuration ====================

    def _get_provider_config(
        self,
        provider_type: str,
        provider_name: str
    ) -> Dict[str, Any]:
        """
        Get provider configuration from Django settings.

        Looks for settings like:
            APOLLO_CONSULTATION_CONFIG = {...}
            ONEMG_PHARMACY_CONFIG = {...}
        """
        # Try specific config first
        config_key = f"{provider_name.upper()}_{provider_type.upper()}_CONFIG"
        config = getattr(settings, config_key, None)

        if config:
            return config

        # Try general provider config
        general_key = f"{provider_name.upper()}_CONFIG"
        config = getattr(settings, general_key, None)

        if config:
            return config

        # Build config from individual settings
        return self._build_config_from_settings(provider_name)

    def _build_config_from_settings(self, provider_name: str) -> Dict[str, Any]:
        """Build provider config from individual settings."""
        prefix = provider_name.upper()
        config = {}

        # Common config keys to look for
        config_keys = [
            'API_BASE_URL', 'API_KEY', 'API_SECRET',
            'CLIENT_ID', 'CLIENT_SECRET', 'MERCHANT_ID',
            'USERNAME', 'PASSWORD', 'TOKEN',
            'WEBHOOK_SECRET', 'API_TIMEOUT', 'AGREEMENT_ID',
        ]

        for key in config_keys:
            setting_name = f"{prefix}_{key}"
            value = getattr(settings, setting_name, None)
            if value is not None:
                # Convert key to lowercase for config dict
                config[key.lower()] = value

        return config

    # ==================== Health Check ====================

    def health_check_all(self) -> Dict[str, Dict[str, bool]]:
        """Check health of all registered providers."""
        results = {
            'consultation': {},
            'diagnostics': {},
            'pharmacy': {},
        }

        for name in self._consultation_providers:
            try:
                provider = self.get_consultation_provider(name)
                results['consultation'][name] = provider.health_check()
            except Exception:
                results['consultation'][name] = False

        for name in self._diagnostics_providers:
            try:
                provider = self.get_diagnostics_provider(name)
                results['diagnostics'][name] = provider.health_check()
            except Exception:
                results['diagnostics'][name] = False

        for name in self._pharmacy_providers:
            try:
                provider = self.get_pharmacy_provider(name)
                results['pharmacy'][name] = provider.health_check()
            except Exception:
                results['pharmacy'][name] = False

        return results


# Global registry instance
provider_registry = ProviderRegistry()


# ==================== Register Providers ====================
# Import and register providers here

def _register_default_providers():
    """Register all default providers."""
    try:
        # Apollo Consultation
        from .apollo.consultation import ApolloConsultationProvider
        provider_registry.register_consultation('apollo', ApolloConsultationProvider)
    except ImportError as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to register Apollo consultation: {e}")

    try:
        # Apollo Diagnostics
        from .apollo.diagnostics import ApolloDiagnosticsProvider
        provider_registry.register_diagnostics('apollo', ApolloDiagnosticsProvider)
    except ImportError as e:
        import logging
        logging.getLogger(__name__).warning(f"Failed to register Apollo diagnostics: {e}")


# Register providers on module load
_register_default_providers()


# Convenience functions
def get_consultation_provider(name: str = None) -> ConsultationProvider:
    """Get a consultation provider (default if name not specified)."""
    if name:
        return provider_registry.get_consultation_provider(name)
    return provider_registry.get_default_consultation_provider()


def get_diagnostics_provider(name: str = None) -> DiagnosticsProvider:
    """Get a diagnostics provider (default if name not specified)."""
    if name:
        return provider_registry.get_diagnostics_provider(name)
    return provider_registry.get_default_diagnostics_provider()


def get_pharmacy_provider(name: str = None) -> PharmacyProvider:
    """Get a pharmacy provider (default if name not specified)."""
    if name:
        return provider_registry.get_pharmacy_provider(name)
    return provider_registry.get_default_pharmacy_provider()
