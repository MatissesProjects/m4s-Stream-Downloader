use the chrome.webRequest API. The extension will listen to the network traffic of the active tab, hunt for the .mpd, .m3u8, or init.mp4/.m4s files, and capture their URLs.

Here is the basic blueprint for an extension using Manifest V3.

1. The Manifest (manifest.json)
This tells Chrome what permissions your extension needs. We need webRequest to sniff the network traffic, and host_permissions to look at the URLs.

JSON
{
  "manifest_version": 3,
  "name": "Stream Catcher",
  "version": "1.0",
  "description": "Intercepts audio streams and manifests.",
  "permissions": [
    "webRequest",
    "downloads"
  ],
  "host_permissions": [
    "<all_urls>"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "action": {
    "default_title": "Audio Intercept"
  }
}
2. The Service Worker (background.js)
This script runs in the background and silently monitors network requests. When it spots a master manifest file or an initialization segment, it logs it.

JavaScript
// Listen for specific file extensions commonly used in media streaming
const targetExtensions = ['.mpd', '.m3u8', 'init.mp4', '.m4s'];

chrome.webRequest.onCompleted.addListener(
  (details) => {
    const url = details.url;
    
    // Check if the URL contains our target stream formats
    if (targetExtensions.some(ext => url.includes(ext))) {
      console.log("Captured Media URL:", url);
      
      // OPTION A: Trigger a direct download of the manifest/segment
      /*
      chrome.downloads.download({
        url: url,
        filename: "captured_stream_data"
      });
      */

      // OPTION B: Send this URL to a local Python server for processing
      /*
      fetch('http://localhost:5000/process_stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ streamUrl: url }),
      }).catch(err => console.error("Local server offline"));
      */
    }
  },
  { urls: ["<all_urls>"] } // Filter: listen to all traffic
);
How to Connect the Dots
Once the extension captures the URL, you have two choices for how to handle the data:

The Browser-Only Route: You can have the extension aggressively download every .m4s segment it sees into a designated folder on your machine. However, you'll still need to stitch them together locally later.

The Python Handoff (Recommended): If you uncomment "Option B" in the code above, the extension acts purely as a scout. It spots the .mpd manifest file and immediately sends a POST request to a lightweight Python Flask or FastAPI server running on your machine. Your Python backend then takes that URL, fires up ffmpeg or yt-dlp, and does the heavy lifting of downloading and converting the final MP3 invisibly in the background.