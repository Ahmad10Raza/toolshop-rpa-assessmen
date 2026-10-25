"""Unit tests for configuration settings and structured logger."""

from pathlib import Path
from unittest.mock import MagicMock
import pytest
from config.settings import get_settings
from utils.logger import setup_logger, log_business_outcome
from utils.retry import execute_with_retry


def test_settings_initialization(tmp_path: Path):
    """Verify settings defaults and directory creation."""
    settings = get_settings()
    assert settings.base_url == "https://practicesoftwaretesting.com"
    assert settings.output_dir.exists()
    assert settings.artifacts_dir.exists()


def test_logger_file_and_business_outcome(tmp_path: Path):
    """Verify logger writes formatted entries to file and correctly tags business outcomes."""
    test_log = tmp_path / "test_run.log"
    logger = setup_logger(test_log, log_level="INFO")

    logger.info("Test standard informational message")
    log_business_outcome(logger, "AUTH_NEGATIVE_TEST", "EXPECTED_REJECTION", "Wrong password rejected")

    assert test_log.exists()
    content = test_log.read_text(encoding="utf-8")

    assert "Test standard informational message" in content
    assert "[BUSINESS_OUTCOME] [AUTH_NEGATIVE_TEST] status='EXPECTED_REJECTION'" in content


def test_execute_with_retry_success(tmp_path: Path):
    """Verify that an action succeeding on attempt 1 does not trigger recovery navigation."""
    mock_page = MagicMock()
    mock_action = MagicMock(return_value="login_ok")

    result = execute_with_retry(
        page=mock_page,
        action_name="test_login",
        action_fn=mock_action,
        recovery_url="https://example.com/login",
        artifacts_dir=tmp_path,
    )

    assert result == "login_ok"
    assert mock_action.call_count == 1
    mock_page.goto.assert_not_called()


def test_execute_with_retry_recovers_after_one_failure(tmp_path: Path):
    """Verify single-attempt recovery navigates to anchor URL and re-executes action."""
    mock_page = MagicMock()
    mock_action = MagicMock(side_effect=[ValueError("Transient DOM timeout"), "recovered_ok"])

    result = execute_with_retry(
        page=mock_page,
        action_name="test_login",
        action_fn=mock_action,
        recovery_url="https://example.com/login",
        artifacts_dir=tmp_path,
    )

    assert result == "recovered_ok"
    assert mock_action.call_count == 2
    mock_page.screenshot.assert_called_once()
    mock_page.goto.assert_called_once_with("https://example.com/login", wait_until="domcontentloaded")
    mock_page.wait_for_load_state.assert_called_once_with("networkidle")


def test_execute_with_retry_fails_after_two_attempts(tmp_path: Path):
    """Verify that permanent errors re-raise the exception after the single retry fails."""
    mock_page = MagicMock()
    mock_action = MagicMock(side_effect=RuntimeError("Permanent selector missing"))

    with pytest.raises(RuntimeError, match="Permanent selector missing"):
        execute_with_retry(
            page=mock_page,
            action_name="test_permanent_failure",
            action_fn=mock_action,
            recovery_url="https://example.com/login",
            artifacts_dir=tmp_path,
        )

    assert mock_action.call_count == 2
    mock_page.screenshot.assert_called_once()
