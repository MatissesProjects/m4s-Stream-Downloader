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
    response = client.post("/download", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "started", "url": "http://example.com/test.mpd"}

def test_clear_all_data():
    # First, populate some data
    client.post("/process", json={"url": "test_url", "sourcePage": "test_page"})
    # Verify it exists (indirectly, via process response count)
    response = client.post("/process", json={"url": "test_url2", "sourcePage": "test_page"})
    assert response.json()["count"] == 2
    
    # Clear it
    response = client.post("/clear")
    assert response.status_code == 200
    assert response.json() == {"status": "cleared"}
    
    # Verify it's gone
    response = client.post("/process", json={"url": "test_url3", "sourcePage": "test_page"})
    assert response.json()["count"] == 1

def test_trigger_stitch():
    # Populate a session
    client.post("/clear")
    client.post("/process", json={"url": "http://segment1", "sourcePage": "test_page"})
    client.post("/process", json={"url": "http://segment2", "sourcePage": "test_page"})
    
    payload = {
        "sourcePage": "test_page",
        "title": "stitched_test"
    }
    response = client.post("/stitch", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "started", "segments": 2}

def test_trigger_stitch_not_found():
    client.post("/clear")
    payload = {
        "sourcePage": "non_existent_page",
        "title": "fail_test"
    }
    response = client.post("/stitch", json=payload)
    assert response.status_code == 404
