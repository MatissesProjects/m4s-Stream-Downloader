// popup.ts

const BACKEND_HEALTH_URL = 'http://localhost:5000/health';
const BACKEND_DOWNLOAD_URL = 'http://localhost:5000/download';

interface CapturedStream {
  url: string;
  sourcePage: string;
  timestamp: string;
  type: string;
}

async function updateUI() {
  const data = await chrome.storage.local.get(['enabled', 'capturedCount', 'capturedStreams']);
  
  const toggle = document.getElementById('interceptor-toggle') as HTMLInputElement;
  const countSpan = document.getElementById('captured-count') as HTMLElement;
  const listContainer = document.getElementById('streams-list') as HTMLElement;
  
  if (toggle) toggle.checked = !!data.enabled;
  if (countSpan) countSpan.textContent = (data.capturedCount || 0).toString();

  if (listContainer) {
    listContainer.innerHTML = '';
    const streams = (data.capturedStreams || []) as CapturedStream[];
    
    if (streams.length === 0) {
      listContainer.innerHTML = '<div style="padding: 10px; font-size: 0.8rem; text-align: center;">No streams captured yet.</div>';
    } else {
      streams.forEach((stream) => {
        const item = document.createElement('div');
        item.className = 'stream-item';
        
        const timestamp = new Date(stream.timestamp).toLocaleTimeString();
        
        item.innerHTML = `
          <div class="stream-header">
            <span class="stream-type">${stream.type}</span>
            <span style="font-size: 0.7rem; color: #999;">${timestamp}</span>
          </div>
          <div class="stream-url" title="${stream.url}">${stream.url}</div>
          <div class="stream-actions">
            <button class="download-btn" data-url="${stream.url}" data-title="${stream.sourcePage}">Download</button>
          </div>
        `;
        listContainer.appendChild(item);
      });

      // Add event listeners to all download buttons
      document.querySelectorAll('.download-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          const target = e.target as HTMLButtonElement;
          const url = target.getAttribute('data-url');
          const title = target.getAttribute('data-title');
          
          if (url) {
            await triggerDownload(url, title || 'downloaded_stream');
          }
        });
      });
    }
  }

  checkBackendStatus();
}

async function triggerDownload(url: string, title: string) {
  try {
    const response = await fetch(BACKEND_DOWNLOAD_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, title })
    });
    
    if (response.ok) {
      alert('Download started in backend!');
    } else {
      alert('Backend error: ' + response.statusText);
    }
  } catch (err) {
    alert('Failed to connect to backend for download.');
  }
}

async function checkBackendStatus() {
  const statusIndicator = document.getElementById('status-indicator');
  if (!statusIndicator) return;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000);

    const response = await fetch(BACKEND_HEALTH_URL, { signal: controller.signal });
    clearTimeout(timeoutId);

    if (response.ok) {
      statusIndicator.textContent = 'Backend Online';
      statusIndicator.className = 'status-indicator status-online';
    } else {
      throw new Error('Offline');
    }
  } catch (err) {
    statusIndicator.textContent = 'Backend Offline';
    statusIndicator.className = 'status-indicator status-offline';
  }
}

document.addEventListener('DOMContentLoaded', () => {
  updateUI();

  const toggle = document.getElementById('interceptor-toggle');
  toggle?.addEventListener('change', (e) => {
    const enabled = (e.target as HTMLInputElement).checked;
    chrome.storage.local.set({ enabled });
  });

  const clearBtn = document.getElementById('clear-btn');
  clearBtn?.addEventListener('click', () => {
    chrome.runtime.sendMessage({ action: 'clearCaptured' }, () => {
      updateUI();
    });
  });

  // Refresh status every 5 seconds
  setInterval(checkBackendStatus, 5000);
});

// Listen for storage changes to update UI
chrome.storage.onChanged.addListener((changes) => {
  if (changes.capturedCount || changes.enabled) {
    updateUI();
  }
});
