import os
import random
import uuid
from celery import Celery
import asyncio
from playwright.async_api import async_playwright
import boto3
import aiofiles
from botocore.exceptions import NoCredentialsError
import dotenv



app = Celery("tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")

SCREEN_DIR = "screens"
os.makedirs(SCREEN_DIR, exist_ok=True)

@app.task
def scrape_and_screenshot(url: str):
    return asyncio.run(_go(url))

async def _go(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        await context.add_init_script("""
Object.defineProperty(navigator, 'webdriver', {
  get: () => false
});
""")

        page = await context.new_page()

        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)

            await page.add_style_tag(content="""
                *[id*='cookie'], *[class*='cookie'] {
                    display: none !important;
                }
            """)

            # Mimic user behavior
            await page.mouse.wheel(0, random.randint(200, 600))
            await page.wait_for_timeout(random.randint(1000, 3000))

        except Exception as e:
            return {"url": url, "error": str(e)}

        filename = f"{uuid.uuid4()}.png"
        path = os.path.join(SCREEN_DIR, filename)
        await page.screenshot(path=path, full_page=True)

        base_path = os.path.dirname(os.path.abspath(__file__))\
        
        path_formatted = os.path.join(base_path, "crawler", path)
        
        with open(path_formatted, 'rb') as file_obj:

            file_url = upload_to_s3(file_obj, AWS_S3_BUCKET_NAME, filename)
        
        await browser.close()

        return {"url": url, "screenshot_path": file_url}


def upload_to_s3(file_obj, bucket, object_name=None):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_S3_KEY_ACCESS_ID,
        aws_secret_access_key=AWS_S3_KEY_SECRET,
        region_name=AWS_S3_REGION
    )

    try:
        s3_client.upload_fileobj(file_obj, bucket, object_name, ExtraArgs={"ContentType": "image/png"})
        
        file_url = f"https://{bucket}.s3.amazonaws.com/{object_name}"
        print(f"Uploaded image to S3: {file_url}")
        return file_url
    except NoCredentialsError:
        print("Credentials not available")
        return None
