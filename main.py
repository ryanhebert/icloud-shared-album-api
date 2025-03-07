import os
from fastapi import FastAPI, HTTPException
import asyncio
from playwright.async_api import async_playwright
import json
from datetime import datetime, timezone
import random
import logging
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
ALBUM_URL = os.getenv('ALBUM_URL')

class ICloudSharedAlbumAPI:
    def __init__(self, album_url):
        self.album_url = album_url
        self.album_data = []
        self.pending_photos = []

    async def _fetch_album_data(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            async def handle_request(response):
                if "sharedstreams" in response.url:
                    try:
                        logging.info(f"Received response from {response.url}")
                        json_data = await response.json()

                        json_string = json.dumps(json_data, indent=2)
                        print(f"JSON Response from Apple:\n{json_string}")
                        logging.info(f"JSON Response from Apple:\n{json_string}")

                        if "items" in json_data and json_data["items"]:
                            json_data["photos"] = self.pending_photos + json_data.get("photos", [])
                            self.pending_photos.clear()
                            self._process_album_data(json_data)
                        else:
                            self.pending_photos.extend(json_data.get("photos", []))
                    except json.JSONDecodeError as e:
                        logging.error(f"Failed to decode JSON from {response.url}: {str(e)}")
                    except Exception as e:
                        logging.error(f"Error processing response from {response.url}: {str(e)}")

            page.on("response", handle_request)
            await page.goto(self.album_url, timeout=60000)
            await asyncio.sleep(5)

            if self.pending_photos:
                self._process_album_data({"photos": self.pending_photos, "items": {}})

            await browser.close()

    def _process_album_data(self, json_data):
        if "photos" not in json_data or not isinstance(json_data["photos"], list):
            return

        photos = json_data["photos"]
        images_info = json_data.get("items", {})
        posts = {}

        for photo in photos:
            batch_guid = photo.get("batchGuid", "unknown")
            caption = photo.get("caption", "No Caption").strip()
            batch_date_created = photo.get("batchDateCreated", "Unknown")
            date_created = photo.get("dateCreated", "Unknown")
            image_objects = []

            if "derivatives" in photo:
                highest_resolution = max(
                    photo["derivatives"].values(),
                    key=lambda d: int(d.get("width", 0)) * int(d.get("height", 0)),
                    default=None
                )
                if highest_resolution:
                    checksum = highest_resolution.get("checksum")
                    if checksum and checksum in images_info:
                        image_data = images_info[checksum]
                        url_location = image_data.get("url_location")
                        url_path = image_data.get("url_path")
                        url_expiry = image_data.get("url_expiry")

                        expiry_minutes = None
                        if url_expiry:
                            expiry_datetime = datetime.strptime(url_expiry, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                            expiry_minutes = max(0, int((expiry_datetime - datetime.now(timezone.utc)).total_seconds() / 60))

                        if url_location and url_path:
                            image_objects.append({
                                "url": f"https://{url_location}{url_path}",
                                "checksum": checksum,
                                "width": highest_resolution.get("width"),
                                "height": highest_resolution.get("height"),
                                "file_size": highest_resolution.get("fileSize"),
                                "created_date": datetime.strptime(photo.get("dateCreated"), "%Y-%m-%dT%H:%M:%SZ").isoformat() if photo.get("dateCreated") else None,
                                "photo_id": photo.get("photoGuid", "Unknown"),
                                "url_expiry": url_expiry,
                                "expires_in_minutes": expiry_minutes
                            })

            if batch_guid not in posts:
                posts[batch_guid] = {
                    "post_date": datetime.strptime(photo.get("batchDateCreated"), "%Y-%m-%dT%H:%M:%SZ").isoformat() if photo.get("batchDateCreated") else None,
                    "caption": caption if caption else None,
                    "num_photos": len(image_objects),
                    "images": image_objects
                }
            else:
                posts[batch_guid]["num_photos"] += len(image_objects)
                posts[batch_guid]["images"].extend(image_objects)
                if not posts[batch_guid]["caption"] and caption:
                    posts[batch_guid]["caption"] = caption

        self.album_data = list(posts.values())

    async def get_album_data(self):
        await self._fetch_album_data()
        return self.album_data

@app.on_event("startup")
async def startup_event():
    logging.info("Fetching iCloud shared album data...")
    api = ICloudSharedAlbumAPI(ALBUM_URL)
    app.state.posts_cache = await api.get_album_data()

    if not app.state.posts_cache:
        logging.warning("No posts were cached. Check if album data is missing.")

@app.get("/recent")
async def recent_posts(limit: int = 5):
    sorted_posts = sorted(app.state.posts_cache, key=lambda x: x["post_date"], reverse=True)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_posts": len(sorted_posts),
        "stream_name": "Public Share Test",
        "album_owner": {
            "first_name": "Ryan",
            "last_name": "Hebert"
        },
        "posts": sorted_posts[:limit]
    }

@app.get("/posts/{post_date}")
async def posts_by_date(post_date: str):
    try:
        query_date = datetime.strptime(post_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    matched_posts = [post for post in app.state.posts_cache if post["post_date"] and datetime.fromisoformat(post["post_date"]).date() == query_date]

    if not matched_posts:
        raise HTTPException(status_code=404, detail="No posts found for the specified date")

    return matched_posts

@app.get("/random")
async def random_post():
    if not app.state.posts_cache:
        raise HTTPException(status_code=404, detail="No posts available")
    return random.choice(app.state.posts_cache)
