import os
os.environ["MOCK_AI"]="true"
from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)

def test_health():
    r=client.get("/health")
    assert r.status_code==200
    assert r.json()["status"]=="ok"

def test_home():
    r=client.get("/")
    assert r.status_code==200
    assert "ComicCraft" in r.text

def test_json_generation_mock():
    payload={"story_prompt":"A brave fox explores an enchanted forest","character_name":"Luna","setting":"Enchanted forest","tone":"Funny","art_style":"Comic book"}
    r=client.post("/generate-comic/json",json=payload)
    assert r.status_code==200
    data=r.json()
    assert len(data["layout"])==5
    assert data["pdf_path"].endswith(".pdf")
