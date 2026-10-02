from typing import List
from pydantic import BaseModel
from .config import get_settings
from .models import PanelOutline, PanelStory, PromptRequest

class StoryResponse(BaseModel):
    panels: List[PanelStory]


def _mock_story(outlines, request):
    result=[]
    for p in outlines:
        result.append(PanelStory(panel_number=p.panel_number, caption=f"{request.tone.title()} moment in {request.setting}.", narration=p.scene_description, dialogue=f"{request.character_name}: We have to keep going!"))
    return result


def generate_story(outlines: List[PanelOutline], request: PromptRequest) -> List[PanelStory]:
    settings=get_settings()
    if settings.mock_ai or not settings.gemini_api_key:
        return _mock_story(outlines, request)
    from google import genai
    from google.genai import types
    client=genai.Client(api_key=settings.gemini_api_key)
    outline_text="\n".join(f"Panel {p.panel_number}: {p.title} — {p.scene_description}" for p in outlines)
    prompt=f"""Expand this 5-panel outline into polished comic narration and dialogue.\nOriginal story: {request.story_prompt}\nCharacter: {request.character_name}\nSetting: {request.setting}\nTone: {request.tone}\nOutline:\n{outline_text}\nFor every panel provide a short ambient caption, 1-3 sentence narration, and concise dialogue. Keep continuity and character identity consistent."""
    response=client.models.generate_content(
        model=settings.gemini_pro_model,
        contents=prompt,
        config=types.GenerateContentConfig(response_mime_type="application/json", response_schema=StoryResponse, temperature=0.85),
    )
    data=StoryResponse.model_validate_json(response.text)
    if len(data.panels)!=5:
        raise ValueError("Gemini did not return story content for all 5 panels")
    return data.panels
