# ComicCraft

ComicCraft turns a story idea into a short, illustrated comic and exports it as a PDF. The app runs locally without AI credentials; optional Gemini and Hugging Face credentials enable model-generated stories and illustrations.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app:app --reload
```

Open <http://127.0.0.1:8000>.

## Optional AI models

Set either or both environment variables before starting the server:

- `GEMINI_API_KEY` enables story generation with Gemini 2.5 Flash.
- `HF_TOKEN` enables image generation through Hugging Face Inference API. `HF_IMAGE_MODEL` can override the default `stabilityai/stable-diffusion-xl-base-1.0` model.

When a model is unavailable or a request fails, ComicCraft uses its built-in story and illustration generators so the comic workflow remains usable.

## API

- `GET /api/health` reports which optional model credentials are configured.
- `POST /api/comics` accepts a prompt, character, setting, tone, art style, and panel count (3-6).
- `POST /api/export` accepts a generated comic and returns a PDF.
- `GET /docs` provides the interactive FastAPI API documentation.