Project Plan: Audio Stream Interceptor & MP3 Converter
1. Objective
Build a two-part system to bypass web player obfuscation and download streaming audio (MPEG-DASH/HLS).

A Chrome Extension to monitor network traffic and capture hidden manifest files (.mpd, .m3u8) or raw data segments (init.mp4, .m4s).

A Local Python Backend to receive the intercepted URLs, stitch the segments, convert them to .mp3, and organize them for immediate use in audio sequencing, mixing, or Twitch streaming setups.

2. Architecture Overview
Frontend (The Scout): Chrome Extension (Manifest V3). Uses chrome.webRequest to sniff network traffic for target file extensions.

Communication Layer: The extension sends a POST request containing the media URL and page context to a local HTTP server running on localhost.

Backend (The Workhorse): A Python API (using Flask or FastAPI) listening for inbound URLs.

Processing Engine: Python triggers yt-dlp (for manifests) or ffmpeg (for raw segments) to download, stitch, and convert the payload into a final MP3 file.

3. Phase 1: The Chrome Extension (Frontend)
Goal: Intercept media URLs silently and pass them to the local server.

Step 1.1: Setup Manifest V3

Define permissions: webRequest, activeTab, scripting.

Define host permissions: <all_urls> (to catch streams on any domain).

Step 1.2: Background Service Worker (background.js)

Implement chrome.webRequest.onCompleted listener.

Filter network traffic for ['.mpd', '.m3u8', 'init.mp4', '.m4s'].

Write the fetch() logic to send captured URLs to http://localhost:5000/process.

Edge Case Handling: Implement a debounce or deduplication logic. A single page load might trigger 50 .m4s requests; we only want to send the master .mpd or the first .m4s to Python to avoid spamming the local server.

Step 1.3: Popup UI (popup.html & popup.js)

Create a simple UI with a toggle switch (Enable/Disable interceptor).

Add a visual status indicator to show if the local Python server is connected.

4. Phase 2: The Python Backend (Backend)
Goal: Receive URLs, download the stream, and process the audio.

Step 2.1: Server Setup

Initialize a lightweight web framework (FastAPI is recommended for speed/async, Flask for simplicity).

Create a POST /process endpoint that accepts JSON {"streamUrl": "...", "sourcePage": "..."}.

Step 2.2: The Download Manager (yt-dlp integration)

Write a handler for .mpd and .m3u8 URLs.

Configure yt-dlp to automatically extract the best audio and convert it to MP3.

Step 2.3: The Fallback Stitcher (ffmpeg integration)

Write a handler for raw .m4s segments (for sites that hide the manifest).

Create a script that downloads the init.mp4 and subsequent .m4s files, concatenates them locally, and runs them through ffmpeg to output an MP3.

Step 2.4: File Management

Define the output directory.

Implement automatic renaming based on a timestamp or the source page title.

5. Phase 3: Testing & Refinement
Step 3.1: Load the unpacked extension into Chrome.

Step 3.2: Start the Python server locally.

Step 3.3: Navigate to a target site with protected audio and verify the extension catches the URL.

Step 3.4: Verify Python successfully downloads, converts, and outputs a playable .mp3 file to the destination folder.

6. Future Expansions (Optional)
Add metadata tagging to the MP3s (Artist, Source URL) before saving.

Create a websocket connection between Python and the Chrome extension to send progress bars (e.g., "Downloading... 50%") back to the extension popup.