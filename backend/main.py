from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import os
import yt_dlp
import requests
from datetime import datetime
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stream-catcher")

app = FastAPI()

# Allow CORS for the extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
TEMP_DIR = os.path.join(os.path.dirname(__file__), "temp")

for d in [DOWNLOAD_DIR, TEMP_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# Session storage: sourcePage -> List[urls]
sessions: Dict[str, List[str]] = {}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/process")
async def process_stream(request: Request):
    data = await request.json()
    url = data.get("url")
    source_page = data.get("sourcePage")
    
    if not url or not source_page:
        return {"error": "Missing url or sourcePage"}, 400

    if source_page not in sessions:
        sessions[source_page] = []
    
    if url not in sessions[source_page]:
        sessions[source_page].append(url)
        logger.info(f"Added to session {source_page}: {url}")
    
    return {"status": "captured", "count": len(sessions[source_page])}

def run_download(url: str, title: str = None):
    """Executes yt-dlp to download and convert the stream (for manifests)."""
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
            logger.info(f"Starting manifest download: {url}")
            ydl.download([url])
            logger.info(f"Download completed for: {url}")
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")

def run_stitch(urls: List[str], title: str = None):
    """Downloads segments and stitches them using ffmpeg."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join([c for c in (title or "session") if c.isalnum() or c in (" ", "_", "-")]).strip()
    session_dir = os.path.join(TEMP_DIR, f"session_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)

    segment_files = []
    logger.info(f"Starting stitch process for {len(urls)} segments.")

    try:
        for i, url in enumerate(urls):
            ext = ".m4s" if ".m4s" in url else (".mp4" if "init" in url else ".bin")
            filename = f"chunk_{i:04d}{ext}"
            filepath = os.path.join(session_dir, filename)
            
            # Simple download
            resp = requests.get(url, stream=True)
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            segment_files.append(filepath)

        # Create ffmpeg concat file
        concat_file = os.path.join(session_dir, "concat.txt")
        with open(concat_file, 'w') as f:
            for sf in segment_files:
                # Use absolute paths and escape single quotes for ffmpeg
                path = os.path.abspath(sf).replace("'", "'\\''")
                f.write(f"file '{path}'\n")

        output_mp3 = os.path.join(DOWNLOAD_DIR, f"{safe_title}_{timestamp}.mp3")
        
        # FFmpeg command: Concatenate segments and convert to MP3
        # -f concat -safe 0: use concat demuxer
        # -i concat.txt: input file list
        # -acodec libmp3lame: convert to mp3
        import subprocess
        cmd = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file,
            '-acodec', 'libmp3lame', '-ab', '192k', output_mp3
        ]
        
        logger.info(f"Running ffmpeg: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Successfully stitched and saved to {output_mp3}")
        else:
            logger.error(f"FFmpeg failed: {result.stderr}")

    except Exception as e:
        logger.error(f"Stitching failed: {str(e)}")
    # Clean up session dir could be added here later

@app.post("/download")
async def trigger_download(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    url = data.get("url")
    title = data.get("title", "downloaded_stream")
    
    if not url:
        raise HTTPException(status_code=400, detail="No URL provided")

    background_tasks.add_task(run_download, url, title)
    return {"status": "started", "url": url}

@app.post("/stitch")
async def trigger_stitch(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    source_page = data.get("sourcePage")
    title = data.get("title", "stitched_session")

    if not source_page or source_page not in sessions:
        raise HTTPException(status_code=404, detail="No segments found for this source page")

    urls = sessions[source_page]
    background_tasks.add_task(run_stitch, urls, title)
    return {"status": "started", "segments": len(urls)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
