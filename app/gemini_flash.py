from typing import List

from pydantic import BaseModel

from .config import get_settings
from .models import PanelOutline, PromptRequest


class OutlineResponse(BaseModel):
    panels: List[PanelOutline]


def _client():
    """Create the Gemini client when an API key is available."""
    from google import genai

    settings = get_settings()

    if not settings.gemini_api_key:
        return None

    return genai.Client(api_key=settings.gemini_api_key)


def _mock_outline(request: PromptRequest) -> List[PanelOutline]:
    """
    Create a story-specific 5-panel outline for demo mode.

    This version uses the user's actual story prompt instead of
    displaying the same generic story for every request.
    """

    story = request.story_prompt.strip()
    character = request.character_name.strip()
    setting = request.setting.strip()
    tone = request.tone.strip()
    art_style = request.art_style.strip()

    panels = [
        {
            "title": "The Beginning",
            "description": (
                f"{character} begins the adventure in {setting}. "
                f"The story introduces the main situation: {story}"
            ),
            "image": (
                f"{character} at the beginning of this story, "
                f"in {setting}, showing the situation described in "
                f"the story: {story}"
            ),
        },
        {
            "title": "The Discovery",
            "description": (
                f"{character} discovers something important connected "
                f"to the story: {story}"
            ),
            "image": (
                f"{character} discovering an important clue or event "
                f"connected to {story}, expressive face, detailed "
                f"{setting} background"
            ),
        },
        {
            "title": "The Challenge",
            "description": (
                f"{character} faces the main challenge and the story "
                f"moves forward: {story}"
            ),
            "image": (
                f"{character} facing the main challenge from {story}, "
                f"dynamic action, dramatic perspective, detailed "
                f"{setting} environment"
            ),
        },
        {
            "title": "The Turning Point",
            "description": (
                f"{character} makes an important decision that changes "
                f"the direction of the story: {story}"
            ),
            "image": (
                f"{character} making a brave and important decision "
                f"during {story}, emotional cinematic comic scene, "
                f"detailed background"
            ),
        },
        {
            "title": "A New Beginning",
            "description": (
                f"The main conflict reaches a conclusion and "
                f"{character} reaches the ending of the story: {story}"
            ),
            "image": (
                f"{character} at the conclusion of {story}, "
                f"meaningful hopeful ending, beautiful {setting}, "
                f"cinematic comic book scene"
            ),
        },
    ]

    result = []

    for index, panel in enumerate(panels, start=1):
        image_prompt = (
            f"{panel['image']}, "
            f"art style: {art_style}, "
            f"tone: {tone}, "
            f"consistent character design across all five panels, "
            f"comic book illustration, clear composition, "
            f"detailed environment"
        )

        result.append(
            PanelOutline(
                panel_number=index,
                title=panel["title"],
                scene_description=panel["description"],
                image_prompt=image_prompt,
            )
        )

    return result


def generate_outline(request: PromptRequest) -> List[PanelOutline]:
    """
    Generate a 5-panel comic outline.

    When MOCK_AI=true, a story-specific demo outline is returned.

    When MOCK_AI=false, Gemini is used to generate the five panels.
    """

    settings = get_settings()

    # Demo / offline mode
    if settings.mock_ai:
        return _mock_outline(request)

    # Real Gemini mode
    client = _client()

    # If Gemini API key is missing, use the demo outline
    # instead of crashing the application.
    if client is None:
        return _mock_outline(request)

    prompt = f"""
Create a coherent five-panel comic story based on the information below.

Story idea:
{request.story_prompt}

Main character:
{request.character_name}

Setting:
{request.setting}

Tone:
{request.tone}

Art style:
{request.art_style}

Requirements:
1. Return exactly five panels.
2. Each panel must continue the same story.
3. Keep the main character visually consistent.
4. Give every panel a short and meaningful title.
5. Give every panel a detailed scene description.
6. Give every panel a detailed image-generation prompt.
7. Make the image prompts suitable for creating comic-book illustrations.
8. The five panels must have a clear beginning, development, challenge,
   turning point, and ending.
"""

    from google.genai import types

    response = client.models.generate_content(
        model=settings.gemini_flash_model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=OutlineResponse,
            temperature=0.9,
        ),
    )

    data = OutlineResponse.model_validate_json(response.text)

    if len(data.panels) != 5:
        raise ValueError("Gemini did not return exactly 5 panels")

    return data.panels