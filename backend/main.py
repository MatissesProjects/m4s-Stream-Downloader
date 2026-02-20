from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging

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

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/process")
async def process_stream(request: Request):
    data = await request.json()
    stream_url = data.get("streamUrl")
    source_page = data.get("sourcePage")
    
    logger.info(f"Received stream URL: {stream_url}")
    logger.info(f"Source Page: {source_page}")
    
    # Placeholder for Phase 2: yt-dlp / ffmpeg processing
    # print(f"Processing {stream_url}...")
    
    return {"status": "received", "url": stream_url}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
