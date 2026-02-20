// popup.ts

const BACKEND_HEALTH_URL = 'http://localhost:5000/health'; // Assuming a health check endpoint

async function updateUI() {
  const data = await chrome.storage.local.get(['enabled', 'capturedCount']);
  
  const toggle = document.getElementById('interceptor-toggle') as HTMLInputElement;
  const countSpan = document.getElementById('captured-count') as HTMLElement;
  
  if (toggle) toggle.checked = !!data.enabled;
  if (countSpan) countSpan.textContent = (data.capturedCount || 0).toString();

  checkBackendStatus();
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
