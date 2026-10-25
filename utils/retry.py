"""Retry engine implementing safe-anchor recovery and failure screenshot capture."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Optional
from playwright.sync_api import Page


def execute_with_retry(
    page: Page,
    action_name: str,
    action_fn: Callable[[], Any],
    recovery_url: Optional[str] = None,
    artifacts_dir: Optional[Path] = None,
    logger: Optional[logging.Logger] = None,
) -> Any:
    """Execute an action with single-attempt retry via anchor navigation and screenshot capture.

    Args:
        page: Playwright Page instance.
        action_name: Identifier for the action used in logs and screenshots.
        action_fn: Callable wrapping the target browser action.
        recovery_url: Safe anchor URL to re-navigate to before retrying.
        artifacts_dir: Directory where failure screenshots are saved.
        logger: Logger instance for recording events.

    Returns:
        The return value of action_fn upon success.

    Raises:
        Exception: If the retry attempt also fails.
    """
    log = logger or logging.getLogger("toolshop_rpa")
    artifacts = artifacts_dir or Path("artifacts")
    artifacts.mkdir(parents=True, exist_ok=True)

    try:
        return action_fn()
    except Exception as initial_error:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_file = artifacts / f"{action_name}_failure_{timestamp}.png"

        try:
            page.screenshot(path=str(screenshot_file), full_page=True)
            log.warning(
                f"[RETRY] Action '{action_name}' failed: {initial_error}. "
                f"Diagnostic screenshot saved to {screenshot_file}"
            )
        except Exception as screen_err:
            log.warning(
                f"[RETRY] Action '{action_name}' failed: {initial_error}. "
                f"Could not capture screenshot: {screen_err}"
            )

        if not recovery_url:
            log.error(f"[RETRY] No recovery URL provided for '{action_name}'. Re-raising exception.")
            raise initial_error

        # Navigate to established anchor page
        log.info(f"[RETRY] Navigating to anchor page '{recovery_url}' to re-establish state...")
        try:
            page.goto(recovery_url, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle")
        except Exception as nav_err:
            log.error(f"[RETRY] Failed to reach anchor URL '{recovery_url}': {nav_err}")
            raise initial_error from nav_err

        # Perform controlled single retry
        log.info(f"[RETRY] Re-executing action '{action_name}' after anchor recovery...")
        return action_fn()
