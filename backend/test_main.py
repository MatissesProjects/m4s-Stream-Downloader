from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_process_stream():
    payload = {
        "streamUrl": "http://example.com/test.mpd",
        "sourcePage": "http://example.com/page",
        "timestamp": "2023-10-27T10:00:00Z"
    }
    response = client.post("/process", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "received", "url": "http://example.com/test.mpd"}
