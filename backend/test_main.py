from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_process_stream():
    payload = {
        "url": "http://example.com/test.mpd",
        "sourcePage": "http://example.com/page",
        "timestamp": "2023-10-27T10:00:00Z"
    }
    response = client.post("/process", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "captured", "count": 1}

def test_trigger_download():
    payload = {
        "url": "http://example.com/test.mpd",
        "title": "My Awesome Stream"
    }
    # We use a background task, so we just check if it returns "started"
    response = client.post("/download", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "started", "url": "http://example.com/test.mpd"}
