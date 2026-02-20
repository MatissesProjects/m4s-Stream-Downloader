from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import os
import yt_dlp
import requests
from datetime import datetime
from typing import Dict, List
import subprocess
import json
import re

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

# Session storage: sessionKey -> List[urls]
sessions: Dict[str, List[str]] = {}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/process")
async def process_stream(request: Request):
    data = await request.json()
    url = data.get("url")
    session_key = data.get("sessionKey")
    
    if not url or not session_key:
        return {"error": "Missing url or sessionKey"}, 400

    if session_key not in sessions:
        sessions[session_key] = []
    
    if url not in sessions[session_key]:
        sessions[session_key].append(url)
        logger.info(f"Added to session {session_key}: {url}")
    
    return {"status": "captured", "count": len(sessions[session_key])}

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

def check_encryption(file_path: str) -> bool:
    """Uses ffprobe to check if the file is encrypted (CENC)."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-show_streams', 
            '-print_format', 'json', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False
            
        data = json.loads(result.stdout)
        for stream in data.get('streams', []):
            if stream.get('is_encrypted') == '1' or 'encryption_scheme' in stream:
                return True
            tags = stream.get('tags', {})
            if any('encrypt' in str(k).lower() or 'encrypt' in str(v).lower() for k, v in tags.items()):
                return True
        return False
    except Exception as e:
        logger.warning(f"Encryption check failed: {str(e)}")
        return False

def run_stitch(urls: List[str], title: str = None):
    """Downloads segments and stitches them using ffmpeg."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join([c for c in (title or "session") if c.isalnum() or c in (" ", "_", "-")]).strip()
    session_dir = os.path.join(TEMP_DIR, f"session_{timestamp}")
    os.makedirs(session_dir, exist_ok=True)

    segment_files = []
    logger.info(f"Starting stitch process for {len(urls)} segments.")

    try:
        def get_sort_key(u: str):
            u_lower = u.lower()
            if 'init' in u_lower:
                return (0, 0)
            numbers = re.findall(r'\d+', u)
            if numbers:
                return (1, int(numbers[-1]))
            return (1, 999999)

        sorted_urls = sorted(urls, key=get_sort_key)
        
        has_init = any('init' in u.lower() for u in sorted_urls)
        if not has_init:
            logger.warning("No 'init' segment found in this session. This may fail.")

        for i, url in enumerate(sorted_urls):
            ext = ".m4s" if ".m4s" in url else (".mp4" if "init" in url else ".bin")
            filename = f"chunk_{i:04d}{ext}"
            filepath = os.path.join(session_dir, filename)

            resp = requests.get(url, stream=True)
            with open(filepath, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            segment_files.append(filepath)

            if i == 0:
                if check_encryption(filepath):
                    logger.error(f"DRM Encryption detected in {url}. Cannot process encrypted streams.")
                    return

        merged_file = os.path.join(session_dir, "merged_segments.tmp")
        with open(merged_file, 'wb') as outfile:
            for sf in segment_files:
                with open(sf, 'rb') as infile:
                    outfile.write(infile.read())

        output_mp3 = os.path.join(DOWNLOAD_DIR, f"{safe_title}_{timestamp}.mp3")
        
        cmd = [
            'ffmpeg', '-y', '-i', merged_file,
            '-acodec', 'libmp3lame', '-ab', '192k', output_mp3
        ]
        
        logger.info(f"Running ffmpeg conversion: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
        
        if result.returncode == 0:
            logger.info(f"Successfully stitched and saved to {output_mp3}")
            if os.path.exists(merged_file):
                os.remove(merged_file)
        else:
            logger.error(f"FFmpeg failed: {result.stderr}")

    except Exception as e:
        logger.error(f"Stitching failed: {str(e)}")

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
    session_key = data.get("sessionKey")
    title = data.get("title", "stitched_session")

    if not session_key or session_key not in sessions:
        raise HTTPException(status_code=404, detail="No segments found for this session")

    urls = list(sessions[session_key])
    del sessions[session_key]
    
    background_tasks.add_task(run_stitch, urls, title)
    return {"status": "started", "segments": len(urls)}

@app.post("/clear")
async def clear_all_data():
    """Clears all session data and removes temporary files."""
    global sessions
    sessions = {}
    logger.info("Cleared all session data.")
    
    import shutil
    try:
        for filename in os.listdir(TEMP_DIR):
            file_path = os.path.join(TEMP_DIR, filename)
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
        logger.info("Successfully cleared TEMP_DIR.")
    except Exception as e:
        logger.error(f"Error clearing TEMP_DIR: {str(e)}")
        
    return {"status": "cleared"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
