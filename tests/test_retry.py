"""Tests for retry logic."""
import pytest
import httpx

from crowe_logic_cli.retry import (
    RetryConfig,
    is_retryable_error,
    with_retry,
    RETRYABLE_STATUS_CODES,
)


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_config(self):
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True

    def test_custom_config(self):
        config = RetryConfig(
            max_retries=5,
            initial_delay=0.5,
            max_delay=30.0,
        )
        assert config.max_retries == 5
        assert config.initial_delay == 0.5
        assert config.max_delay == 30.0

    def test_calculate_delay_no_jitter(self):
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=False,
        )
        assert config.calculate_delay(0) == 1.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 4.0
        assert config.calculate_delay(3) == 8.0

    def test_calculate_delay_respects_max(self):
        config = RetryConfig(
            initial_delay=1.0,
            max_delay=5.0,
            exponential_base=2.0,
            jitter=False,
        )
        assert config.calculate_delay(10) == 5.0

    def test_calculate_delay_with_jitter(self):
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            jitter=True,
        )
        # With jitter, delay should be between 0.5 * base_delay and 1.5 * base_delay
        delay = config.calculate_delay(0)
        assert 0.5 <= delay <= 1.5


class TestIsRetryableError:
    """Tests for is_retryable_error function."""

    def test_timeout_exception_is_retryable(self):
        config = RetryConfig()
        error = httpx.TimeoutException("timeout")
        assert is_retryable_error(error, config) is True

    def test_network_error_is_retryable(self):
        config = RetryConfig()
        error = httpx.NetworkError("network")
        assert is_retryable_error(error, config) is True

    def test_generic_exception_not_retryable(self):
        config = RetryConfig()
        error = ValueError("not retryable")
        assert is_retryable_error(error, config) is False

    def test_retryable_status_codes(self):
        # These status codes should be retryable
        expected_retryable = {408, 429, 500, 502, 503, 504}
        assert RETRYABLE_STATUS_CODES == expected_retryable


class TestWithRetry:
    """Tests for with_retry decorator."""

    def test_succeeds_first_try(self):
        call_count = 0

        @with_retry(verbose=False)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_func()
        assert result == "success"
        assert call_count == 1

    def test_retries_on_failure(self):
        call_count = 0
        config = RetryConfig(max_retries=2, initial_delay=0.01, jitter=False)

        @with_retry(config=config, verbose=False)
        def failing_then_succeeding():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TimeoutException("timeout")
            return "success"

        result = failing_then_succeeding()
        assert result == "success"
        assert call_count == 2

    def test_gives_up_after_max_retries(self):
        call_count = 0
        config = RetryConfig(max_retries=2, initial_delay=0.01, jitter=False)

        @with_retry(config=config, verbose=False)
        def always_failing():
            nonlocal call_count
            call_count += 1
            raise httpx.TimeoutException("timeout")

        with pytest.raises(httpx.TimeoutException):
            always_failing()

        # Initial call + 2 retries = 3 total calls
        assert call_count == 3

    def test_non_retryable_error_not_retried(self):
        call_count = 0
        config = RetryConfig(max_retries=3, initial_delay=0.01)

        @with_retry(config=config, verbose=False)
        def non_retryable_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            non_retryable_error()

        assert call_count == 1
