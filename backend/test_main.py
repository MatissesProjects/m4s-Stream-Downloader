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
        "sessionKey": "test_session",
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
    response = client.post("/download", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "started", "url": "http://example.com/test.mpd"}

def test_clear_all_data():
    # Start clean
    client.post("/clear")
    # First, populate some data
    client.post("/process", json={"url": "test_url", "sessionKey": "test_session"})
    # Verify it exists (indirectly, via process response count)
    response = client.post("/process", json={"url": "test_url2", "sessionKey": "test_session"})
    assert response.json()["count"] == 2
    
    # Clear it
    response = client.post("/clear")
    assert response.status_code == 200
    assert response.json() == {"status": "cleared"}
    
    # Verify it's gone
    response = client.post("/process", json={"url": "test_url3", "sessionKey": "test_session"})
    assert response.json()["count"] == 1

def test_trigger_stitch():
    # Populate a session
    client.post("/clear")
    client.post("/process", json={"url": "http://segment1", "sessionKey": "test_session"})
    client.post("/process", json={"url": "http://segment2", "sessionKey": "test_session"})
    
    payload = {
        "sessionKey": "test_session",
        "title": "stitched_test"
    }
    response = client.post("/stitch", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "started", "segments": 2}

def test_trigger_stitch_not_found():
    client.post("/clear")
    payload = {
        "sessionKey": "non_existent_session",
        "title": "fail_test"
    }
    response = client.post("/stitch", json=payload)
    assert response.status_code == 404
