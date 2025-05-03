from __future__ import annotations

import os, uuid, random, asyncio
from pathlib import Path
from typing import List

import boto3
from botocore.exceptions import NoCredentialsError
from playwright.async_api import async_playwright, Page, Browser
from app.tools.models.screenshot_model import ScreenshotRequest, ScreenshotResult

# ───────────────────────────── config via env vars ──────────────────────────
SCREEN_DIR         = Path(os.getenv("SCREEN_DIR", "./screenshots"))
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_S3_KEY_ACCESS  = os.getenv("AWS_S3_KEY_ACCESS_ID")
AWS_S3_KEY_SECRET  = os.getenv("AWS_S3_KEY_SECRET")
AWS_S3_REGION      = os.getenv("AWS_S3_REGION", "us-east-1")

SCREEN_DIR.mkdir(exist_ok=True, parents=True)


# ───────────────────────────── helper functions ────────────────────────────
def _upload_to_s3(file_path: Path) -> str | None:
    s3 = boto3.client(
        "s3",
        aws_access_key_id=AWS_S3_KEY_ACCESS,
        aws_secret_access_key=AWS_S3_KEY_SECRET,
        region_name=AWS_S3_REGION,
    )
    try:
        s3.upload_file(str(file_path), AWS_S3_BUCKET_NAME, file_path.name,
                       ExtraArgs={"ContentType": "image/png"})
        return f"https://{AWS_S3_BUCKET_NAME}.s3.amazonaws.com/{file_path.name}"
    except NoCredentialsError:
        return None


async def _capture_one(page_url: str) -> ScreenshotResult:
    async with async_playwright() as p:
        browser: Browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => false})"
        )
        page: Page = await context.new_page()

        try:
            await page.goto(page_url, wait_until="domcontentloaded", timeout=60_000)
            # hide cookie banners
            await page.add_style_tag(content="*[id*='cookie'], *[class*='cookie'] {display:none!important;}")
            # mimic user scroll
            await page.mouse.wheel(0, random.randint(200, 600))
            await page.wait_for_timeout(random.randint(1000, 3000))

            fname = f"{uuid.uuid4()}.png"
            local_path = SCREEN_DIR / fname
            await page.screenshot(path=str(local_path), full_page=True)
            s3_url = _upload_to_s3(local_path)

            result = ScreenshotResult(
                original_url=page_url,
                screenshot_url=s3_url or "",
            )
        except Exception as exc:
            result = ScreenshotResult(
                original_url=page_url,
                screenshot_url="",
                error=str(exc),
            )
        finally:
            await browser.close()

        return result


# ─────────────────────── public API used by the MCP tool ────────────────────
async def take_screenshots(reqs: List[ScreenshotRequest]) -> List[ScreenshotResult]:
    tasks = [_capture_one(r.url) for r in reqs]
    # run 3 at a time to avoid hammering Playwright resources
    semaphore = asyncio.Semaphore(3)

    async def _guard(task):
        async with semaphore:
            return await task

    results = await asyncio.gather(*[_guard(t) for t in tasks])
    return results
