from typing import List
from pydantic import BaseModel, Field

class PromptRequest(BaseModel):
    story_prompt: str = Field(min_length=3, max_length=2000)
    character_name: str = Field(min_length=1, max_length=100)
    setting: str = Field(min_length=1, max_length=200)
    tone: str = Field(min_length=1, max_length=50)
    art_style: str = Field(min_length=1, max_length=100)

class PanelOutline(BaseModel):
    panel_number: int
    title: str
    scene_description: str
    image_prompt: str

class PanelStory(BaseModel):
    panel_number: int
    caption: str
    narration: str
    dialogue: str

class ComicLayoutItem(BaseModel):
    panel_number: int
    title: str
    image_path: str
    scene_description: str
    image_prompt: str
    caption: str
    narration: str
    dialogue: str

class ComicResponse(BaseModel):
    title: str
    layout: List[ComicLayoutItem]
    pdf_path: str
