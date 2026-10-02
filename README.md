# ComicCraft — AI Comic Story Creator

ComicCraft is a FastAPI + Jinja2 web application based on the supplied project documentation. It accepts a story prompt, character name, setting, tone and art style, then creates a five-panel comic outline, narration/dialogue, illustrations and a PDF export.

## Architecture

- **Frontend:** HTML + CSS + Jinja2
- **Backend:** FastAPI + Uvicorn
- **Story outline:** Gemini Flash via the modern `google-genai` SDK
- **Narration/dialogue:** Gemini Pro via the same SDK
- **Images:** Hugging Face Inference Providers using a text-to-image diffusion model
- **PDF:** FPDF2
- **Demo fallback:** If AI keys are absent, the app automatically generates deterministic placeholder panels so the complete UI and PDF flow can still be tested.

The supplied documentation originally names Gemini 1.5 Flash/Pro and `google-generativeai`. This implementation keeps the same Flash → Pro → diffusion architecture, but uses the current Google GenAI Python SDK and configurable model names so the project is easier to maintain.

## Folder structure

```text
ComicCraft/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── routes.py
│   ├── gemini_flash.py
│   ├── gemini_pro.py
│   ├── image_generator.py
│   ├── layout_builder.py
│   └── exporters.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── comic_preview.html
│   └── export_success.html
├── static/
│   ├── css/style.css
│   ├── js/app.js
│   ├── panels/
│   └── exports/
├── tests/test_app.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Windows + VS Code setup

1. Install Python 3.11 or newer.
2. Open this folder in VS Code.
3. Open **Terminal → New Terminal**.
4. Create a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

5. Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

6. Create your environment file:

```powershell
copy .env.example .env
```

7. For a no-key first test, edit `.env` and set:

```text
MOCK_AI=true
```

8. Start the server:

```powershell
uvicorn app.main:app --reload
```

9. Open:

- http://127.0.0.1:8000 — web application
- http://127.0.0.1:8000/docs — Swagger API documentation
- http://127.0.0.1:8000/health — health check

## Enable real AI generation

Set `MOCK_AI=false`, then add your credentials to `.env`:

```text
GEMINI_API_KEY=your_key
HF_TOKEN=your_huggingface_token
```

The Google GenAI SDK reads the API key supplied by the application, and Hugging Face's `InferenceClient` uses the HF token for image inference.

## API example

POST `/generate-comic/json` with:

```json
{
  "story_prompt": "A brave fox exploring an enchanted forest",
  "character_name": "Luna",
  "setting": "Enchanted forest",
  "tone": "Dramatic",
  "art_style": "Anime"
}
```

## Test

With the virtual environment active:

```powershell
pytest -q
```

## Common errors

### `pip install -r requirements.txt` says `__pycache__/` is an invalid requirement
Your `requirements.txt` contains a folder name accidentally. Replace it with the `requirements.txt` in this project, which contains only package requirements.

### `GEMINI_API_KEY` error
Check `.env`, make sure the key is correct, and restart Uvicorn after changing environment variables.

### Image generation error
Check `HF_TOKEN` and `HF_IMAGE_MODEL`. You can temporarily set `MOCK_AI=true` to test the rest of the application without external image inference.

### PowerShell says `uvicorn` is not recognized
Make sure `.venv` is activated, then run:

```powershell
python -m uvicorn app.main:app --reload
```

## GitHub

After testing locally:

```powershell
git init
git add .
git commit -m "Initial ComicCraft project"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ComicCraft.git
git push -u origin main
```

Never commit `.env`; it is excluded by `.gitignore`.
