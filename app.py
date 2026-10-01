import asyncio
import base64
import io
import json
import os
import re
from pathlib import Path
from typing import Literal

import httpx
from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fpdf import FPDF
from PIL import Image, ImageDraw
from pydantic import BaseModel, Field
from starlette.staticfiles import StaticFiles

ROOT = Path(__file__).parent
app = FastAPI(title="ComicCraft", version="1.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


class ComicRequest(BaseModel):
    prompt: str = Field(min_length=8, max_length=1200)
    character: str = Field(default="Milo", min_length=1, max_length=80)
    setting: str = Field(default="An enchanted forest", min_length=1, max_length=120)
    tone: str = Field(default="Heartfelt", max_length=40)
    art_style: str = Field(default="Comic book", max_length=40)
    panel_count: int = Field(default=4, ge=3, le=6)


class Panel(BaseModel):
    title: str
    narration: str
    dialogue: str
    image_prompt: str
    image: str


class Comic(BaseModel):
    title: str
    prompt: str
    character: str
    setting: str
    tone: str
    art_style: str
    panels: list[Panel]
    story_provider: str
    image_provider: str


class ExportRequest(BaseModel):
    comic: Comic


def _fallback_story(request: ComicRequest) -> list[dict[str, str]]:
    character = request.character.strip()
    beats = [
        ("A curious beginning", f"When {character} set out through {request.setting.lower()}, the ordinary path ended sooner than expected.", "I wonder what's waiting out there."),
        ("Something stirs", f"A strange clue appeared, and {character} followed it into the heart of the adventure.", "That definitely wasn't here before."),
        ("The brave choice", f"At the turning point, {character} trusted a new friend and faced the challenge together.", "We can do this. Together."),
        ("A brighter ending", f"By sunset, the world felt bigger, kinder, and full of stories still to come.", "Tomorrow, let's take the long way home."),
        ("One more surprise", f"Just as the adventure seemed over, {character} spotted one last curious sign in the distance.", "Did you see that?"),
        ("A new path", f"With a smile and a pocketful of memories, {character} stepped toward the next chapter.", "Our next adventure starts now."),
    ]
    selected_beats = [
        beats[round(position * (len(beats) - 1) / (request.panel_count - 1))]
        for position in range(request.panel_count)
    ]
    return [
        {"title": title, "narration": narration, "dialogue": dialogue,
         "image_prompt": f"{request.art_style} illustration, {request.tone.lower()} mood, {request.character} in {request.setting}, {request.prompt}, scene {index + 1}"}
        for index, (title, narration, dialogue) in enumerate(selected_beats)
    ]


def _parse_story(text: str, count: int) -> list[dict[str, str]]:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    payload = json.loads(cleaned)
    panels = payload.get("panels", payload) if isinstance(payload, dict) else payload
    if not isinstance(panels, list) or len(panels) < count:
        raise ValueError("Gemini returned an incomplete comic")
    return [
        {key: str(item.get(key, "")) for key in ("title", "narration", "dialogue", "image_prompt")}
        for item in panels[:count]
    ]


async def _gemini_story(request: ComicRequest) -> list[dict[str, str]] | None:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    instruction = (
        "Write a cohesive comic as JSON only, with this shape: "
        '{"panels":[{"title":"...","narration":"...","dialogue":"...",'
        '"image_prompt":"..."}]}. Make exactly the requested number of panels. '
        "Keep narration concise, dialogue natural, and image prompts visually specific. "
        f"Story idea: {request.prompt}\nMain character: {request.character}\n"
        f"Setting: {request.setting}\nTone: {request.tone}\nArt style: {request.art_style}\n"
        f"Panel count: {request.panel_count}"
    )
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                url,
                params={"key": api_key},
                json={"contents": [{"parts": [{"text": instruction}]}],
                      "generationConfig": {"responseMimeType": "application/json", "temperature": 0.85}},
            )
            response.raise_for_status()
            text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return _parse_story(text, request.panel_count)
    except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError):
        return None


def _illustration(index: int, request: ComicRequest) -> str:
    width, height = 960, 620
    palettes = {
        "comic book": ((79, 196, 218), (244, 119, 83), (251, 211, 77)),
        "anime": ((173, 221, 243), (255, 133, 149), (255, 227, 137)),
        "watercolor": ((178, 220, 190), (231, 153, 137), (247, 221, 151)),
        "pixel art": ((128, 196, 166), (237, 111, 82), (255, 212, 95)),
        "storybook": ((161, 209, 190), (229, 130, 103), (250, 219, 150)),
    }
    sky, accent, sun = palettes.get(request.art_style.lower(), palettes["comic book"])
    image = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(image)
    horizon = 395 + (index % 2) * 24
    for y in range(height):
        blend = y / height
        bottom = (245, 224, 177)
        color = tuple(round(sky[channel] * (1 - blend) + bottom[channel] * blend) for channel in range(3))
        draw.line((0, y, width, y), fill=color)
    draw.ellipse((710 - index * 18, 62, 850 - index * 18, 202), fill=sun)
    draw.ellipse((-100, horizon - 40, 470, 650), fill=(92, 169, 129))
    draw.ellipse((380, horizon - 5, 1080, 700), fill=(62, 135, 113))
    if any(word in request.setting.lower() for word in ("forest", "wood", "jungle")):
        for x, y, size in [(80, 258, 105), (205, 225, 130), (786, 245, 112), (895, 220, 142)]:
            draw.rectangle((x - 12, y + size // 2, x + 12, height), fill=(87, 103, 76))
            draw.ellipse((x - size // 2, y - size // 2, x + size // 2, y + size // 2), fill=(42, 119, 91))
    elif any(word in request.setting.lower() for word in ("city", "town", "street")):
        for x, building_width, building_height in [(55, 115, 205), (795, 130, 275), (665, 92, 165)]:
            draw.rectangle((x, horizon - building_height, x + building_width, horizon + 65), fill=(75, 109, 128))
            for wx in range(x + 18, x + building_width - 10, 34):
                for wy in range(horizon - building_height + 22, horizon, 42):
                    draw.rectangle((wx, wy, wx + 13, wy + 19), fill=(247, 207, 111))
    else:
        for x in (105, 215, 755, 865):
            draw.ellipse((x - 5, horizon - 100, x + 110, horizon + 25), fill=(68, 147, 111))
    center = 460 + ((index % 3) - 1) * 92
    draw.ellipse((center - 128, 454, center + 128, 514), fill=(48, 102, 84))
    draw.ellipse((center - 76, 300, center + 76, 474), fill=accent, outline=(28, 41, 42), width=8)
    draw.ellipse((center - 58, 222, center + 58, 342), fill=accent, outline=(28, 41, 42), width=8)
    draw.polygon([(center - 49, 250), (center - 39, 173), (center - 2, 238)], fill=accent, outline=(28, 41, 42))
    draw.polygon([(center + 15, 238), (center + 46, 173), (center + 52, 260)], fill=accent, outline=(28, 41, 42))
    draw.ellipse((center - 30, 270, center - 20, 282), fill=(28, 41, 42))
    draw.ellipse((center + 20, 270, center + 30, 282), fill=(28, 41, 42))
    draw.arc((center - 18, 278, center + 18, 306), start=10, end=170, fill=(28, 41, 42), width=4)
    draw.line((center - 42, 448, center - 54, 495), fill=(28, 41, 42), width=12)
    draw.line((center + 42, 448, center + 54, 495), fill=(28, 41, 42), width=12)
    for offset, star_y in [(-245, 205), (-184, 300), (205, 242), (270, 340)]:
        star_x = (center + offset) % width
        draw.line((star_x - 12, star_y, star_x + 12, star_y), fill=(255, 251, 229), width=5)
        draw.line((star_x, star_y - 12, star_x, star_y + 12), fill=(255, 251, 229), width=5)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


async def _huggingface_image(prompt: str) -> str | None:
    token = os.getenv("HF_TOKEN")
    if not token:
        return None
    model = os.getenv("HF_IMAGE_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")
    url = f"https://router.huggingface.co/hf-inference/models/{model}"
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(
                url,
                headers={"Authorization": f"Bearer {token}"},
                json={"inputs": prompt, "parameters": {"width": 960, "height": 620}},
            )
            response.raise_for_status()
        if not response.headers.get("content-type", "").startswith("image/"):
            return None
        return "data:image/png;base64," + base64.b64encode(response.content).decode("ascii")
    except httpx.HTTPError:
        return None


@app.get("/")
async def home() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/health")
async def health() -> dict[str, str | bool]:
    return {"status": "ok", "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
            "huggingface_configured": bool(os.getenv("HF_TOKEN"))}


@app.post("/api/comics", response_model=Comic)
async def create_comic(request: ComicRequest) -> Comic:
    story = await _gemini_story(request)
    panels = story or _fallback_story(request)
    image_results = await asyncio.gather(*[
        _huggingface_image(panel["image_prompt"]) for panel in panels
    ])
    image_provider = "Hugging Face + local art" if any(image_results) else "ComicCraft studio art"
    result_panels = [
        Panel(**panel, image=image or _illustration(index, request))
        for index, (panel, image) in enumerate(zip(panels, image_results))
    ]
    title = panels[0]["title"] if panels else "A ComicCraft Adventure"
    return Comic(title=title, prompt=request.prompt, character=request.character,
                 setting=request.setting, tone=request.tone, art_style=request.art_style,
                 panels=result_panels, story_provider="Gemini 2.5 Flash" if story else "ComicCraft story studio",
                 image_provider=image_provider)


@app.post("/api/export")
async def export_comic(request: ExportRequest) -> Response:
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    bold_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    unicode_font = font_path.exists() and bold_path.exists()
    if unicode_font:
        pdf.add_font("ComicSans", fname=str(font_path))
        pdf.add_font("ComicSans", style="B", fname=str(bold_path))

    for number, panel in enumerate(request.comic.panels, start=1):
        pdf.add_page()
        pdf.set_fill_color(19, 43, 47)
        pdf.rect(0, 0, 210, 36, style="F")
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("ComicSans" if unicode_font else "Helvetica", "B", 17)
        pdf.set_xy(15, 11)
        pdf.cell(135, 10, f"{number:02d}  {panel.title[:60]}")
        pdf.set_font("ComicSans" if unicode_font else "Helvetica", "", 9)
        pdf.set_xy(153, 13)
        pdf.cell(42, 8, f"PANEL {number:02d} / {len(request.comic.panels):02d}", align="R")

        image_payload = panel.image.partition(",")[2]
        try:
            image_bytes = base64.b64decode(image_payload, validate=True)
            with Image.open(io.BytesIO(image_bytes)) as source:
                converted = io.BytesIO()
                source.convert("RGB").save(converted, format="JPEG", quality=88)
            converted.seek(0)
            pdf.image(converted, x=15, y=46, w=180, h=116)
        except (ValueError, OSError):
            pdf.set_fill_color(226, 243, 237)
            pdf.rect(15, 46, 180, 116, style="F")

        pdf.set_text_color(35, 56, 56)
        pdf.set_font("ComicSans" if unicode_font else "Helvetica", "", 12)
        pdf.set_xy(18, 173)
        pdf.multi_cell(174, 7, panel.narration)
        if panel.dialogue:
            pdf.set_fill_color(239, 248, 237)
            pdf.set_draw_color(200, 221, 211)
            quote_y = max(pdf.get_y() + 9, 207)
            pdf.set_xy(15, quote_y)
            pdf.multi_cell(180, 10, f"\"{panel.dialogue}\"", border=1, fill=True, align="C")

        pdf.set_text_color(95, 117, 112)
        pdf.set_font("ComicSans" if unicode_font else "Helvetica", "", 8)
        pdf.set_xy(15, 282)
        pdf.cell(180, 5, f"{request.comic.character}  /  {request.comic.setting}  /  {request.comic.art_style}")

    filename = re.sub(r"[^a-zA-Z0-9_-]+", "-", request.comic.character.lower()).strip("-") or "comic"
    content = bytes(pdf.output())
    return Response(content=content, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="comiccraft-{filename}.pdf"'})
