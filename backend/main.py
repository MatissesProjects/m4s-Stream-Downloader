from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import os
import yt_dlp
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stream-catcher")

app = FastAPI()

# Allow CORS for the extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your extension ID
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/process")
async def process_stream(request: Request):
    data = await request.json()
    stream_url = data.get("streamUrl")
    source_page = data.get("sourcePage")
    
    logger.info(f"Captured stream URL: {stream_url}")
    # Extension will soon send more info, but for now we just log it.
    return {"status": "captured", "url": stream_url}

def run_download(url: str, title: str = None):
    """Executes yt-dlp to download and convert the stream."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join([c for c in (title or "stream") if c.isalnum() or c in (" ", "_", "-")]).strip()
    output_template = os.path.join(DOWNLOAD_DIR, f"{safe_title}_{timestamp}.%(ext)s")

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_template,
        'quiet': False,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Starting download: {url}")
            ydl.download([url])
            logger.info(f"Download completed for: {url}")
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")

@app.post("/download")
async def trigger_download(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    stream_url = data.get("url")
    title = data.get("title", "downloaded_stream")
    
    if not stream_url:
        return {"error": "No URL provided"}, 400

    background_tasks.add_task(run_download, stream_url, title)
    return {"status": "started", "url": stream_url}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
