import asyncio
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright

async def playwright_crawl(url: str, wait_selector: Optional[str] = None, scroll: bool = False) -> Dict[str, Any]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            response = await page.goto(url, timeout=20000)
            # Handle cookie dialogs (simple)
            try:
                await page.click('button:has-text("Accept")', timeout=2000)
            except Exception:
                pass
            # Wait for dynamic content
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=5000)
                except Exception:
                    pass
            # Infinite scroll
            if scroll:
                for _ in range(10):
                    await page.mouse.wheel(0, 10000)
                    await asyncio.sleep(0.5)
            html = await page.content()
            title = await page.title()
            return {
                "url": url,
                "title": title,
                "html": html,
                "status": response.status if response else None,
            }
        finally:
            await browser.close() 