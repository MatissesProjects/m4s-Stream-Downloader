// background.ts

const TARGET_EXTENSIONS = ['.mpd', '.m3u8', 'init.mp4', '.m4s'];
const BACKEND_URL = 'http://localhost:5000/process';
const MAX_CAPTURES = 50;

interface CapturedStream {
  url: string;
  sourcePage: string;
  timestamp: string;
  type: string;
}

interface AppState {
  enabled: boolean;
  capturedCount: number;
  capturedStreams: CapturedStream[];
}

// Initialize state
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({ enabled: true, capturedCount: 0, capturedStreams: [] });
});

// Cache for deduplication (temporary in-memory for the session)
const capturedUrls = new Set<string>();

function getFileType(url: string): string {
  if (url.includes('.mpd')) return 'DASH (.mpd)';
  if (url.includes('.m3u8')) return 'HLS (.m3u8)';
  if (url.includes('init.mp4') || url.includes('.m4s')) return 'Segment (.m4s)';
  return 'Unknown';
}

chrome.webRequest.onCompleted.addListener(
  async (details) => {
    const state = await chrome.storage.local.get(['enabled', 'capturedStreams']) as AppState;
    if (!state.enabled) return;

    const url = details.url;
    if (TARGET_EXTENSIONS.some(ext => url.includes(ext))) {
      if (capturedUrls.has(url)) return;

      capturedUrls.add(url);
      console.log('Captured Media URL:', url);

      const newStream: CapturedStream = {
        url,
        sourcePage: details.initiator || 'unknown',
        timestamp: new Date().toISOString(),
        type: getFileType(url)
      };

      const updatedStreams = [newStream, ...(state.capturedStreams || [])].slice(0, MAX_CAPTURES);

      await chrome.storage.local.set({ 
        capturedCount: updatedStreams.length,
        capturedStreams: updatedStreams
      });

      // Send to local Python backend (notify only)
      try {
        fetch(BACKEND_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(newStream),
        }).catch(() => {}); // Ignore errors if backend is offline
      } catch (err) {}
    }
  },
  { urls: ['<all_urls>'] }
);

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'clearCaptured') {
    capturedUrls.clear();
    chrome.storage.local.set({ capturedCount: 0, capturedStreams: [] });
    sendResponse({ success: true });
  }
});
