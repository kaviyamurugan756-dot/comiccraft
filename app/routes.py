from pathlib import Path
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from .models import PromptRequest
from .gemini_flash import generate_outline
from .gemini_pro import generate_story
from .image_generator import generate_image
from .layout_builder import build_comic_layout
from .exporters import save_pdf

router=APIRouter()
templates=Jinja2Templates(directory="templates")


def _generate(request_data: PromptRequest):
    outlines=generate_outline(request_data)
    stories=generate_story(outlines, request_data)
    images=[generate_image(p.image_prompt, p.panel_number) for p in outlines]
    layout=build_comic_layout(outlines, stories, images)
    title=f"{request_data.character_name}'s Comic Adventure"
    pdf_path=save_pdf(title, layout)
    return title, layout, pdf_path

@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"title":"ComicCraft"})

@router.post("/generate")
async def generate(request: Request, story_prompt: str=Form(...), character_name: str=Form(...), setting: str=Form(...), tone: str=Form(...), art_style: str=Form(...)):
    try:
        data=PromptRequest(story_prompt=story_prompt, character_name=character_name, setting=setting, tone=tone, art_style=art_style)
        title, layout, pdf_path=_generate(data)
        return templates.TemplateResponse(request=request, name="comic_preview.html", context={"title":title,"layout":layout,"pdf_path":pdf_path})
    except Exception as exc:
        return templates.TemplateResponse(request=request, name="index.html", context={"title":"ComicCraft","error":str(exc)}, status_code=500)

@router.post("/generate-comic/json")
async def generate_json(payload: PromptRequest):
    try:
        title, layout, pdf_path=_generate(payload)
        return {"title":title,"layout":[p.model_dump() for p in layout],"pdf_path":pdf_path}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@router.get("/export-success")
async def export_success(request: Request):
    return templates.TemplateResponse(request=request, name="export_success.html", context={"title":"Export Complete"})

@router.get("/test-image")
async def test_image(request: Request, prompt: str="A brave fox in an enchanted forest, comic book style"):
    try:
        path=generate_image(prompt, 0)
        return {"prompt":prompt,"image_path":path}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
