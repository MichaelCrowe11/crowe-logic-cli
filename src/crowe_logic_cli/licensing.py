"""License management and feature gating for Crowe Logic CLI.

Tier Structure:
- Free: Basic features, rate limited
- Pro: Full features, priority support
- Enterprise: Team features, SSO, audit logs
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class LicenseTier(str, Enum):
    """License tier levels."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class LicenseInfo:
    """License information."""
    tier: LicenseTier
    email: Optional[str] = None
    organization: Optional[str] = None
    expires_at: Optional[str] = None
    issued_at: Optional[str] = None
    features: list[str] = field(default_factory=list)
    limits: dict[str, Any] = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        """Check if license is expired."""
        if not self.expires_at:
            return False
        try:
            expiry = datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
            return datetime.now(timezone.utc) > expiry
        except ValueError:
            return True

    @property
    def is_valid(self) -> bool:
        """Check if license is valid."""
        return not self.is_expired

    def has_feature(self, feature: str) -> bool:
        """Check if license has a specific feature."""
        # Enterprise has all features
        if self.tier == LicenseTier.ENTERPRISE:
            return True
        # Pro has most features
        if self.tier == LicenseTier.PRO:
            return feature not in ENTERPRISE_ONLY_FEATURES
        # Free tier - check explicit features
        return feature in self.features or feature in FREE_FEATURES

    def get_limit(self, limit_name: str, default: Any = None) -> Any:
        """Get a usage limit value."""
        tier_limits = TIER_LIMITS.get(self.tier, {})
        return self.limits.get(limit_name) or tier_limits.get(limit_name, default)


# Feature definitions
FREE_FEATURES = frozenset({
    "chat",
    "ask",
    "interactive",
    "history",
    "config",
    "doctor",
})

PRO_FEATURES = frozenset({
    "quantum",
    "molecular",
    "research",
    "code_analysis",
    "agents",
    "plugins",
    "cost_tracking",
    "output_formats",
    "retry_logic",
    "clipboard",
    "mcp",
})

ENTERPRISE_ONLY_FEATURES = frozenset({
    "sso",
    "audit_logs",
    "team_sharing",
    "priority_support",
    "custom_models",
    "api_access",
    "usage_analytics",
    "role_based_access",
})

# Usage limits per tier
TIER_LIMITS: dict[LicenseTier, dict[str, Any]] = {
    LicenseTier.FREE: {
        "requests_per_day": 50,
        "requests_per_hour": 10,
        "max_tokens_per_request": 4096,
        "history_retention_days": 7,
        "max_conversations": 10,
    },
    LicenseTier.PRO: {
        "requests_per_day": 1000,
        "requests_per_hour": 100,
        "max_tokens_per_request": 32000,
        "history_retention_days": 90,
        "max_conversations": 100,
    },
    LicenseTier.ENTERPRISE: {
        "requests_per_day": None,  # Unlimited
        "requests_per_hour": None,  # Unlimited
        "max_tokens_per_request": 128000,
        "history_retention_days": 365,
        "max_conversations": None,  # Unlimited
    },
}


class LicenseManager:
    """Manage license validation and feature gating."""

    # This would be your actual license server public key in production
    LICENSE_SERVER_URL = "https://api.crowelogic.com/licenses"
    GRACE_PERIOD_DAYS = 7

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        """Initialize license manager.

        Args:
            data_dir: Directory for storing license data
        """
        if data_dir is None:
            data_dir = Path.home() / ".crowelogic"
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._license_file = self.data_dir / "license.json"
        self._license: Optional[LicenseInfo] = None
        self._load()

    def _load(self) -> None:
        """Load license from disk."""
        if self._license_file.exists():
            try:
                with open(self._license_file, "r") as f:
                    data = json.load(f)
                    self._license = LicenseInfo(
                        tier=LicenseTier(data.get("tier", "free")),
                        email=data.get("email"),
                        organization=data.get("organization"),
                        expires_at=data.get("expires_at"),
                        issued_at=data.get("issued_at"),
                        features=data.get("features", []),
                        limits=data.get("limits", {}),
                    )
            except (json.JSONDecodeError, KeyError, ValueError):
                self._license = None

    def _save(self) -> None:
        """Save license to disk."""
        if self._license:
            data = {
                "tier": self._license.tier.value,
                "email": self._license.email,
                "organization": self._license.organization,
                "expires_at": self._license.expires_at,
                "issued_at": self._license.issued_at,
                "features": self._license.features,
                "limits": self._license.limits,
            }
            with open(self._license_file, "w") as f:
                json.dump(data, f, indent=2)

    @property
    def license(self) -> LicenseInfo:
        """Get current license (returns free tier if none)."""
        if self._license and self._license.is_valid:
            return self._license
        return LicenseInfo(tier=LicenseTier.FREE)

    @property
    def tier(self) -> LicenseTier:
        """Get current tier."""
        return self.license.tier

    def activate(self, license_key: str) -> tuple[bool, str]:
        """Activate a license key.

        Args:
            license_key: The license key to activate

        Returns:
            Tuple of (success, message)
        """
        # In production, this would call your license server
        # For now, we support a simple offline key format

        try:
            license_info = self._validate_offline_key(license_key)
            if license_info:
                self._license = license_info
                self._save()
                return True, f"License activated: {license_info.tier.value.upper()} tier"
            return False, "Invalid license key"
        except Exception as e:
            return False, f"Activation failed: {str(e)}"

    def _validate_offline_key(self, key: str) -> Optional[LicenseInfo]:
        """Validate an offline license key.

        Offline key format: TIER-EMAIL_HASH-EXPIRY-SIGNATURE
        Example: PRO-abc123-20251231-xyz789

        In production, use proper cryptographic signatures.
        """
        try:
            parts = key.split("-")
            if len(parts) < 3:
                return None

            tier_str = parts[0].lower()
            if tier_str not in [t.value for t in LicenseTier]:
                return None

            tier = LicenseTier(tier_str)

            # Parse expiry if present
            expires_at = None
            if len(parts) >= 3 and parts[2].isdigit():
                year = int(parts[2][:4])
                month = int(parts[2][4:6])
                day = int(parts[2][6:8])
                expires_at = f"{year}-{month:02d}-{day:02d}T23:59:59Z"

            return LicenseInfo(
                tier=tier,
                expires_at=expires_at,
                issued_at=datetime.now(timezone.utc).isoformat(),
                features=list(PRO_FEATURES) if tier != LicenseTier.FREE else [],
            )
        except Exception:
            return None

    def deactivate(self) -> None:
        """Deactivate current license."""
        self._license = None
        if self._license_file.exists():
            self._license_file.unlink()

    def check_feature(self, feature: str) -> tuple[bool, str]:
        """Check if a feature is available.

        Args:
            feature: Feature name to check

        Returns:
            Tuple of (allowed, message)
        """
        license_info = self.license

        if license_info.has_feature(feature):
            return True, ""

        if feature in PRO_FEATURES:
            return False, f"Feature '{feature}' requires Pro license. Upgrade at https://crowelogic.com/pricing"

        if feature in ENTERPRISE_ONLY_FEATURES:
            return False, f"Feature '{feature}' requires Enterprise license. Contact sales@crowelogic.com"

        return False, f"Unknown feature: {feature}"

    def check_limit(self, limit_name: str, current_value: int) -> tuple[bool, str]:
        """Check if a usage limit is exceeded.

        Args:
            limit_name: Name of the limit to check
            current_value: Current usage value

        Returns:
            Tuple of (allowed, message)
        """
        license_info = self.license
        limit = license_info.get_limit(limit_name)

        if limit is None:  # Unlimited
            return True, ""

        if current_value < limit:
            return True, ""

        return False, f"Limit reached: {limit_name} ({current_value}/{limit}). Upgrade for higher limits."

    def print_status(self, console: Optional[Console] = None) -> None:
        """Print license status to console."""
        if console is None:
            console = Console()

        license_info = self.license

        # Status panel
        tier_colors = {
            LicenseTier.FREE: "white",
            LicenseTier.PRO: "green",
            LicenseTier.ENTERPRISE: "gold1",
        }
        tier_color = tier_colors.get(license_info.tier, "white")

        console.print(f"\n[bold {tier_color}]License: {license_info.tier.value.upper()}[/bold {tier_color}]")

        if license_info.email:
            console.print(f"  Email: {license_info.email}")
        if license_info.organization:
            console.print(f"  Organization: {license_info.organization}")
        if license_info.expires_at:
            console.print(f"  Expires: {license_info.expires_at[:10]}")
            if license_info.is_expired:
                console.print("  [red]⚠ License expired[/red]")

        # Limits table
        console.print("\n[bold]Usage Limits:[/bold]")
        limits_table = Table(show_header=True, header_style="bold")
        limits_table.add_column("Limit")
        limits_table.add_column("Value", justify="right")

        for limit_name, limit_value in TIER_LIMITS.get(license_info.tier, {}).items():
            display_value = "Unlimited" if limit_value is None else str(limit_value)
            limits_table.add_row(limit_name.replace("_", " ").title(), display_value)

        console.print(limits_table)

        # Features table
        console.print("\n[bold]Available Features:[/bold]")
        features_table = Table(show_header=True, header_style="bold")
        features_table.add_column("Feature")
        features_table.add_column("Status", justify="center")

        all_features = sorted(FREE_FEATURES | PRO_FEATURES | ENTERPRISE_ONLY_FEATURES)
        for feature in all_features:
            if license_info.has_feature(feature):
                features_table.add_row(feature, "[green]✓[/green]")
            else:
                features_table.add_row(feature, "[dim]✗[/dim]")

        console.print(features_table)

        # Upgrade prompt
        if license_info.tier == LicenseTier.FREE:
            console.print(Panel(
                "[bold]Upgrade to Pro for:[/bold]\n"
                "• Quantum-enhanced reasoning\n"
                "• Code analysis & review\n"
                "• Molecular dynamics\n"
                "• Research tools\n"
                "• Higher rate limits\n\n"
                "[link=https://crowelogic.com/pricing]https://crowelogic.com/pricing[/link]",
                title="[yellow]Upgrade Available[/yellow]",
                border_style="yellow",
            ))


# Decorator for feature gating
def require_feature(feature: str):
    """Decorator to require a feature for a command.

    Usage:
        @require_feature("quantum")
        def quantum_command():
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_license_manager()
            allowed, message = manager.check_feature(feature)
            if not allowed:
                console = Console()
                console.print(f"[red]✗ {message}[/red]")
                raise SystemExit(1)
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Global license manager instance
_manager: Optional[LicenseManager] = None


def get_license_manager() -> LicenseManager:
    """Get or create global license manager instance."""
    global _manager
    if _manager is None:
        _manager = LicenseManager()
    return _manager
