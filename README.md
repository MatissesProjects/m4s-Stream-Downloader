# m4sStreamDownloader

A two-part tool (Chrome Extension + Python Backend) designed to intercept, stitch, and convert streaming audio (MPEG-DASH/HLS) into playable MP3 files.

## Overview

Modern web players often obfuscate audio streams by breaking them into small segments (`.m4s`, `.mp4`) or hiding them behind manifest files (`.mpd`, `.m3u8`). **m4sStreamDownloader** bypasses these hurdles by:
1. **Intercepting** the network requests directly from your browser.
2. **Forwarding** the URLs to a local Python server.
3. **Stitching** the segments together and **converting** them using `ffmpeg` or `yt-dlp`.

---

## Features

- **Network Sniffing:** Automatically detects `.m4s`, `.mp4` (init segments), `.mpd`, and `.m3u8` files.
- **Manifest Support:** Downloads full streams from manifest files using `yt-dlp`.
- **Raw Segment Stitching:** Manually collects and concatenates raw media segments when manifests are unavailable.
- **MP3 Conversion:** High-quality conversion (192kbps) using `ffmpeg`.
- **Encryption Detection:** Checks for Common Encryption (CENC/DRM) to identify protected streams that cannot be processed.
- **Asynchronous Processing:** Downloads and conversions run in the background without blocking the UI.

---

## Prerequisites

- **Python 3.8+**
- **Node.js & npm** (for building the extension)
- **FFmpeg:** Must be installed and available in your system's `PATH`.
- **Chrome Browser:** For running the extension.

---

## Installation

### 1. Backend Setup
Navigate to the `backend` directory and install the dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### 2. Extension Setup
Install Node dependencies and build the extension:
```bash
npm install
npm run build
```

---

## Usage

### 1. Start the Backend
From the `backend` directory:
```bash
python main.py
```
The server will start on `http://localhost:5000`.

### 2. Load the Chrome Extension
1. Open Chrome and go to `chrome://extensions/`.
2. Enable **Developer mode** (top right).
3. Click **Load unpacked**.
4. Select the `extension/` folder in this project directory.

### 3. Capture Streams
1. Navigate to the website containing the audio stream.
2. Open the **m4sStreamDownloader** extension popup.
3. As you play the audio, you will see segments or manifests appearing in the "Captured Streams" list.
4. Click **Download Manifest** (for `.mpd`/`.m3u8`) or **Stitch & Download** (for collected segments).
5. Files will be saved in `backend/downloads/`.

---

## Limitations

- **DRM/Encryption:** This tool cannot decrypt streams protected by Widevine, PlayReady, or FairPlay (Common Encryption/CENC). If the backend detects encryption, the process will stop to avoid outputting corrupted data.
- **Dynamic URLs:** Some sites use highly ephemeral URLs or complex authentication headers that may expire before the backend can process them.
- **Segment Gaps:** If the extension misses the "init" segment or intermediate chunks due to network timing, the stitching may fail.

---

## Development

- **Build Extension:** `npm run build`
- **Watch Mode:** `npm run watch` (rebuilds extension on file changes)
- **Test Backend:** `npm run test` (runs pytest in the backend directory)

## License
ISC License. See `package.json` for details.
