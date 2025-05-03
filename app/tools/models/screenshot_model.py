from __future__ import annotations
from pydantic import BaseModel, HttpUrl
from typing import List


class ScreenshotRequest(BaseModel):
    url: HttpUrl            # page we should capture


class ScreenshotResult(BaseModel):
    original_url: HttpUrl
    screenshot_url: HttpUrl
    error: str | None = None
