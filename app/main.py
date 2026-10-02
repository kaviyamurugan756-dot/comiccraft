from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .config import get_settings
from .routes import router

BASE_DIR=Path(__file__).resolve().parent.parent
settings=get_settings()
app=FastAPI(title=settings.app_name, version="1.0.0", description="Generate personalized 5-panel comics with Gemini and Hugging Face image generation.")
app.mount("/static", StaticFiles(directory=str(BASE_DIR/"static")), name="static")
app.include_router(router)

@app.get("/health")
def health():
    return {"status":"ok","service":"ComicCraft"}
