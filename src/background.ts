// background.ts

const TARGET_EXTENSIONS = ['.mpd', '.m3u8', 'init.mp4', '.m4s'];
const BACKEND_URL = 'http://localhost:5000/process';

interface AppState {
  enabled: boolean;
  capturedCount: number;
}

// Initialize state
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({ enabled: true, capturedCount: 0 });
});

// Cache for deduplication (temporary in-memory for the session)
const capturedUrls = new Set<string>();

chrome.webRequest.onCompleted.addListener(
  async (details) => {
    const { enabled } = await chrome.storage.local.get('enabled') as AppState;
    if (!enabled) return;

    const url = details.url;
    if (TARGET_EXTENSIONS.some(ext => url.includes(ext))) {
      if (capturedUrls.has(url)) return;

      capturedUrls.add(url);
      console.log('Captured Media URL:', url);

      // Update count in storage
      const { capturedCount } = await chrome.storage.local.get('capturedCount') as AppState;
      await chrome.storage.local.set({ capturedCount: (capturedCount || 0) + 1 });

      // Send to local Python backend
      try {
        const response = await fetch(BACKEND_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            streamUrl: url,
            sourcePage: details.initiator || 'unknown',
            timestamp: new Date().toISOString()
          }),
        });

        if (!response.ok) {
          console.error('Backend responded with error:', response.statusText);
        }
      } catch (err) {
        console.error('Local server offline or unreachable:', err);
      }
    }
  },
  { urls: ['<all_urls>'] }
);

// Listen for messages from popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'clearCaptured') {
    capturedUrls.clear();
    chrome.storage.local.set({ capturedCount: 0 });
    sendResponse({ success: true });
  }
});
