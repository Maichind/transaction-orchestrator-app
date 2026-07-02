"""
Wikipedia RPA Scraper — Playwright automation.

Flow:
  1. Open Wikipedia search for a given term
  2. Extract the first meaningful paragraph from the article
  3. POST the text to /assistant/summarize
  4. Print the AI summary
 
Why robust selectors instead of XPath?
- `#mw-content-text p` is stable across Wikipedia's HTML over years
- CSS selectors survive minor DOM restructuring better than XPath
- Playwright's auto-wait eliminates explicit sleeps (no time.sleep)

Usage:
    python wikipedia_scraper.py "Python programming language"
    python wikipedia_scraper.py "FastAPI"
    python wikipedia_scraper.py                  # defaults to "Celery task queue"
"""
from __future__ import annotations
import os
import sys
import json
import httpx
import asyncio
from typing import Any
from dotenv import load_dotenv
from base_scraper import BaseScraper, ScraperError

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
WIKIPEDIA_BASE = "https://en.wikipedia.org/wiki"
MIN_PARAGRAPH_LENGTH = 80  # chars — skip stubs and navigation paragraphs


class WikipediaScraper(BaseScraper):
    """
    Scrapes the first substantial paragraph from a Wikipedia article
    and sends it to the /assistant/summarize endpoint.
    """

    def __init__(self) -> None:
        super().__init__(name="WikipediaScraper")

    async def scrape(self, term: str) -> dict[str, Any]:  # type: ignore[override]
        """
        Scrape Wikipedia for `term` and summarize via the backend API.

        Returns:
            {
                "success": bool,
                "term": str,
                "url": str,
                "article_title": str,
                "extracted_text": str,
                "summary": SummarizeResponse | None,
                "error": str | None,
            }
        """
        assert self.page is not None

        result: dict[str, Any] = {
            "success": False,
            "term": term,
            "url": "",
            "article_title": "",
            "extracted_text": "",
            "summary": None,
            "error": None,
        }

        try:
            # ── Step 1: Navigate to Wikipedia article ─────────────────────────
            # Use the wiki URL directly (more reliable than the search UI)
            slug = term.replace(" ", "_")
            url = f"{WIKIPEDIA_BASE}/{slug}"
            result["url"] = url

            await self.navigate(url)
            self._log(f"Page loaded: {url}")

            # ── Step 2: Extract article title ─────────────────────────────────
            # #firstHeading is stable across all Wikipedia skins
            title_el = self.page.locator("#firstHeading")
            await title_el.wait_for(state="visible")
            title = (await title_el.inner_text()).strip()
            result["article_title"] = title
            self._log(f"Article title: {title}")

            # ── Step 3: Handle disambiguation pages ───────────────────────────
            disambiguation = self.page.locator(".disambigbox, .dmbox-disambig")
            if await disambiguation.count() > 0:
                self._log("Disambiguation page detected — taking first article link")
                first_link = self.page.locator(
                    "#mw-content-text .mw-parser-output ul li a"
                ).first
                await first_link.click()
                await self.page.wait_for_load_state("domcontentloaded")
                title = (await self.page.locator("#firstHeading").inner_text()).strip()
                result["article_title"] = title
                result["url"] = self.page.url
                self._log(f"Followed to: {title}")

            # ── Step 4: Extract first meaningful paragraph ────────────────────
            # Target: paragraphs inside the article body, skip empty/short ones
            # The selector avoids infoboxes, navboxes and hatnotes
            paragraphs = self.page.locator(
                "#mw-content-text > .mw-parser-output > p"
            )
            count = await paragraphs.count()
            self._log(f"Found {count} paragraph elements")

            first_paragraph = ""
            for i in range(min(count, 10)):  # scan first 10 at most
                raw = (await paragraphs.nth(i).inner_text()).strip()
                # Strip footnote markers like [1] [2]
                cleaned = _clean_wikipedia_text(raw)
                if len(cleaned) >= MIN_PARAGRAPH_LENGTH:
                    first_paragraph = cleaned
                    self._log(
                        f"Extracted paragraph #{i+1} ({len(first_paragraph)} chars)"
                    )
                    break

            if not first_paragraph:
                raise ScraperError(
                    f"No substantial paragraph found for '{term}' "
                    f"(checked {min(count, 10)} elements)"
                )

            result["extracted_text"] = first_paragraph
            self._log(f"Text preview: {first_paragraph[:120]}…")

            # ── Step 5: Send to /assistant/summarize ──────────────────────────
            summary_response = await _call_summarize_api(first_paragraph)
            result["summary"] = summary_response
            result["success"] = True

            self._log("✓ Scrape and summarize complete")

        except ScraperError as exc:
            result["error"] = str(exc)
            self._log(f"✗ ScraperError: {exc}")
        except Exception as exc:
            result["error"] = f"Unexpected error: {exc}"
            self._log(f"✗ Unexpected: {exc}")

        return result


# ── Helpers ────────────────────────────────────────────────────────────────────
def _clean_wikipedia_text(text: str) -> str:
    """Remove Wikipedia citation markers like [1], [note 2], etc."""
    import re
    # Remove [n] style footnotes
    text = re.sub(r'\[\d+\]', '', text)
    # Remove [note n], [a], etc.
    text = re.sub(r'\[[a-z](?:\s\d+)?\]', '', text)
    # Collapse multiple spaces
    text = re.sub(r'  +', ' ', text)
    return text.strip()


async def _call_summarize_api(text: str) -> dict[str, Any]:
    """
    POST to /assistant/summarize and return the response dict.
    Uses httpx async client for non-blocking I/O.
    """
    url = f"{API_BASE_URL}/assistant/summarize"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json={"text": text})
        response.raise_for_status()
        return response.json()


# ── Entry point ────────────────────────────────────────────────────────────────
async def main() -> None:
    term = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Celery task queue"

    print(f"\n{'='*60}")
    print(f"  Wikipedia RPA Scraper")
    print(f"  Term: \"{term}\"")
    print(f"  API:  {API_BASE_URL}")
    print(f"{'='*60}\n")

    async with WikipediaScraper() as scraper:
        result = await scraper.scrape(term)

    print(f"\n{'='*60}")
    print(f"  RESULT")
    print(f"{'='*60}")

    if result["success"]:
        print(f"\n📖 Article : {result['article_title']}")
        print(f"🔗 URL     : {result['url']}")
        print(f"\n📝 Extracted text ({len(result['extracted_text'])} chars):")
        print(f"   {result['extracted_text'][:300]}…")

        if result["summary"]:
            s = result["summary"]
            print(f"\n✨ AI Summary ({s.get('source', '?')} · {s.get('tokens_used', 0)} tokens):")
            print(f"   {s.get('summary', '')}")
            print(f"\n   Log ID : {s.get('id', '')}")
            print(f"   Mock   : {s.get('is_mock', True)}")
    else:
        print(f"\n✗ Failed: {result['error']}")

    print(f"\n{'='*60}")
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    asyncio.run(main())
