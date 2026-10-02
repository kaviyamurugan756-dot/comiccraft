from typing import List
from .models import PanelOutline, PanelStory, ComicLayoutItem

def build_comic_layout(outlines: List[PanelOutline], stories: List[PanelStory], image_paths: List[str]) -> List[ComicLayoutItem]:
    story_map={s.panel_number:s for s in stories}
    layout=[]
    for i,p in enumerate(outlines):
        s=story_map[p.panel_number]
        layout.append(ComicLayoutItem(panel_number=p.panel_number,title=p.title,image_path=image_paths[i],scene_description=p.scene_description,image_prompt=p.image_prompt,caption=s.caption,narration=s.narration,dialogue=s.dialogue))
    return layout
