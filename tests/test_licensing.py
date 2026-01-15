"""Tests for licensing module."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from crowe_logic_cli.licensing import (
    LicenseInfo,
    LicenseManager,
    LicenseTier,
    FREE_FEATURES,
    PRO_FEATURES,
    ENTERPRISE_ONLY_FEATURES,
    TIER_LIMITS,
    get_license_manager,
)


class TestLicenseTier:
    """Tests for LicenseTier enum."""

    def test_tier_values(self):
        assert LicenseTier.FREE.value == "free"
        assert LicenseTier.PRO.value == "pro"
        assert LicenseTier.ENTERPRISE.value == "enterprise"


class TestLicenseInfo:
    """Tests for LicenseInfo dataclass."""

    def test_free_tier_default(self):
        info = LicenseInfo(tier=LicenseTier.FREE)
        assert info.tier == LicenseTier.FREE
        assert info.is_valid
        assert not info.is_expired

    def test_expired_license(self):
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        info = LicenseInfo(tier=LicenseTier.PRO, expires_at=yesterday)
        assert info.is_expired
        assert not info.is_valid

    def test_valid_license(self):
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        info = LicenseInfo(tier=LicenseTier.PRO, expires_at=tomorrow)
        assert not info.is_expired
        assert info.is_valid

    def test_has_feature_free_tier(self):
        info = LicenseInfo(tier=LicenseTier.FREE)
        # Free features should be available
        assert info.has_feature("chat")
        assert info.has_feature("ask")
        # Pro features should not be available
        assert not info.has_feature("quantum")
        assert not info.has_feature("molecular")

    def test_has_feature_pro_tier(self):
        info = LicenseInfo(tier=LicenseTier.PRO)
        # All free and pro features should be available
        assert info.has_feature("chat")
        assert info.has_feature("quantum")
        assert info.has_feature("molecular")
        # Enterprise features should not be available
        assert not info.has_feature("sso")
        assert not info.has_feature("audit_logs")

    def test_has_feature_enterprise_tier(self):
        info = LicenseInfo(tier=LicenseTier.ENTERPRISE)
        # All features should be available
        assert info.has_feature("chat")
        assert info.has_feature("quantum")
        assert info.has_feature("sso")
        assert info.has_feature("audit_logs")

    def test_get_limit(self):
        info = LicenseInfo(tier=LicenseTier.FREE)
        assert info.get_limit("requests_per_day") == 50
        assert info.get_limit("nonexistent", default=999) == 999


class TestFeatureDefinitions:
    """Tests for feature definitions."""

    def test_free_features_defined(self):
        assert "chat" in FREE_FEATURES
        assert "ask" in FREE_FEATURES
        assert "interactive" in FREE_FEATURES

    def test_pro_features_defined(self):
        assert "quantum" in PRO_FEATURES
        assert "molecular" in PRO_FEATURES
        assert "research" in PRO_FEATURES

    def test_enterprise_features_defined(self):
        assert "sso" in ENTERPRISE_ONLY_FEATURES
        assert "audit_logs" in ENTERPRISE_ONLY_FEATURES

    def test_no_feature_overlap(self):
        # Features should be in exactly one tier
        assert len(FREE_FEATURES & PRO_FEATURES) == 0
        assert len(FREE_FEATURES & ENTERPRISE_ONLY_FEATURES) == 0
        assert len(PRO_FEATURES & ENTERPRISE_ONLY_FEATURES) == 0


class TestTierLimits:
    """Tests for tier limits."""

    def test_free_limits(self):
        limits = TIER_LIMITS[LicenseTier.FREE]
        assert limits["requests_per_day"] == 50
        assert limits["requests_per_hour"] == 10

    def test_pro_limits(self):
        limits = TIER_LIMITS[LicenseTier.PRO]
        assert limits["requests_per_day"] == 1000
        assert limits["requests_per_hour"] == 100

    def test_enterprise_limits(self):
        limits = TIER_LIMITS[LicenseTier.ENTERPRISE]
        assert limits["requests_per_day"] is None  # Unlimited
        assert limits["requests_per_hour"] is None  # Unlimited


class TestLicenseManager:
    """Tests for LicenseManager class."""

    @pytest.fixture
    def temp_manager(self, tmp_path):
        """Create a LicenseManager with a temporary directory."""
        return LicenseManager(data_dir=tmp_path)

    def test_default_to_free_tier(self, temp_manager):
        assert temp_manager.tier == LicenseTier.FREE
        assert temp_manager.license.tier == LicenseTier.FREE

    def test_activate_valid_key(self, temp_manager):
        success, message = temp_manager.activate("PRO-test-20271231")
        assert success
        assert temp_manager.tier == LicenseTier.PRO

    def test_activate_invalid_key(self, temp_manager):
        success, message = temp_manager.activate("invalid")
        assert not success
        assert temp_manager.tier == LicenseTier.FREE

    def test_deactivate(self, temp_manager):
        temp_manager.activate("PRO-test-20271231")
        assert temp_manager.tier == LicenseTier.PRO

        temp_manager.deactivate()
        assert temp_manager.tier == LicenseTier.FREE

    def test_check_feature_allowed(self, temp_manager):
        allowed, message = temp_manager.check_feature("chat")
        assert allowed
        assert message == ""

    def test_check_feature_blocked(self, temp_manager):
        allowed, message = temp_manager.check_feature("quantum")
        assert not allowed
        assert "Pro" in message or "upgrade" in message.lower()

    def test_check_limit_under(self, temp_manager):
        allowed, message = temp_manager.check_limit("requests_per_day", 10)
        assert allowed

    def test_check_limit_over(self, temp_manager):
        allowed, message = temp_manager.check_limit("requests_per_day", 100)
        assert not allowed
        assert "Limit reached" in message

    def test_persistence(self, tmp_path):
        # Create manager and activate
        manager1 = LicenseManager(data_dir=tmp_path)
        manager1.activate("PRO-test-20271231")
        assert manager1.tier == LicenseTier.PRO

        # Create new manager with same directory
        manager2 = LicenseManager(data_dir=tmp_path)
        assert manager2.tier == LicenseTier.PRO


class TestGetLicenseManager:
    """Tests for global license manager."""

    def test_returns_manager(self):
        manager = get_license_manager()
        assert isinstance(manager, LicenseManager)

    def test_singleton(self):
        manager1 = get_license_manager()
        manager2 = get_license_manager()
        assert manager1 is manager2
