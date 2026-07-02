"""
BaseScraper — reusable async Playwright wrapper.

Design decisions:
- async context manager → guarantees browser.close() even on exceptions
- headless=True default, overridable via env var for debugging
- Retry logic at the page navigation level (transient network errors)
- Structured logging for observability during automation runs

Usage:
    async with WikipediaScraper() as scraper:
        result = await scraper.scrape("Python programming language")
"""
from __future__ import annotations
import os
from abc import ABC, abstractmethod
from typing import Any
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
    TimeoutError as PlaywrightTimeoutError,
)

# ── Config ─────────────────────────────────────────────────────────────────────
HEADLESS = os.getenv("RPA_HEADLESS", "true").lower() == "true"
SLOW_MO  = int(os.getenv("RPA_SLOW_MO", "0"))       # ms between actions (debug)
TIMEOUT  = int(os.getenv("RPA_TIMEOUT_MS", "15000")) # page/element timeout
RETRIES  = int(os.getenv("RPA_RETRIES", "3"))


class ScraperError(Exception):
    """Raised when a scraping operation fails after all retries."""


class BaseScraper(ABC):
    """
    Async context manager base for Playwright scrapers.

    Concrete scrapers override `scrape()` and use `self.page`.
    The base class owns browser lifecycle entirely.
    """

    def __init__(self, name: str = "BaseScraper") -> None:
        self.name = name
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self.page: Page | None = None

    async def __aenter__(self) -> "BaseScraper":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=HEADLESS,
            slow_mo=SLOW_MO,
        )
        self._context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (compatible; TechnicalAssessmentBot/1.0; "
                "+https://github.com/example/assessment)"
            ),
            java_script_enabled=True,
        )
        self._context.set_default_timeout(TIMEOUT)
        self.page = await self._context.new_page()
        self._log(f"Browser ready — headless={HEADLESS}")
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self.page:
            await self.page.close()
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._log("Browser closed")

    @abstractmethod
    async def scrape(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """
        Implement scraping logic in concrete subclasses.
        Always returns a dict with at minimum: { "success": bool, "data": ... }
        """

    async def navigate(self, url: str, wait_until: str = "domcontentloaded") -> None:
        """Navigate with retry on transient failures."""
        assert self.page is not None, "Page not initialized — use as context manager"
        last_exc: Exception | None = None
 
        for attempt in range(1, RETRIES + 1):
            try:
                self._log(f"Navigating to {url} (attempt {attempt})")
                await self.page.goto(url, wait_until=wait_until)
                return
            except PlaywrightTimeoutError as exc:
                self._log(f"Timeout on attempt {attempt}: {exc}")
                last_exc = exc
            except Exception as exc:
                self._log(f"Navigation error on attempt {attempt}: {exc}")
                last_exc = exc
 
        raise ScraperError(
            f"Failed to navigate to {url} after {RETRIES} attempts: {last_exc}"
        )

    def _log(self, message: str) -> None:
        print(f"[{self.name}] {message}")
