import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .config import get_settings

BASE_DIR=Path(__file__).resolve().parent.parent
PANELS_DIR=BASE_DIR / "static" / "panels"
PANELS_DIR.mkdir(parents=True, exist_ok=True)


def _safe_name(text):
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", text).strip("_")[:60] or "panel"


def _placeholder(prompt, panel_number):
    image=Image.new("RGB", (1024, 1024), "#f7f1df")
    draw=ImageDraw.Draw(image)
    try:
        font=ImageFont.truetype("arial.ttf", 34)
        small=ImageFont.truetype("arial.ttf", 22)
    except OSError:
        font=ImageFont.load_default(); small=font
    draw.rectangle((25,25,999,999), outline="#171717", width=8)
    draw.text((55,60), f"COMICCRAFT • PANEL {panel_number}", fill="#171717", font=font)
    words=prompt[:500]
    draw.multiline_text((55,180), words, fill="#333333", font=small, spacing=12)
    draw.text((55,900), "Image placeholder — add HF_TOKEN for AI illustrations", fill="#555555", font=small)
    return image


def generate_image(prompt: str, panel_number: int) -> str:
    settings=get_settings()
    filename=f"panel_{panel_number}_{_safe_name(prompt)}.png"
    path=PANELS_DIR/filename
    if settings.mock_ai or not settings.hf_token:
        _placeholder(prompt, panel_number).save(path)
        return f"/static/panels/{filename}"
    from huggingface_hub import InferenceClient
    client=InferenceClient(provider="auto", api_key=settings.hf_token)
    image=client.text_to_image(prompt=prompt, model=settings.hf_image_model)
    image.save(path)
    return f"/static/panels/{filename}"
