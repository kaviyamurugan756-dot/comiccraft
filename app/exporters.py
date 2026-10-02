from pathlib import Path
from datetime import datetime
import textwrap
from fpdf import FPDF
from .models import ComicLayoutItem

BASE_DIR=Path(__file__).resolve().parent.parent
EXPORT_DIR=BASE_DIR/"static"/"exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _local_image_path(web_path: str) -> Path:
    return BASE_DIR / web_path.lstrip("/").replace("/", "/")


def _pdf_text(value: str) -> str:
    return "\n".join(textwrap.wrap(str(value), width=95, break_long_words=True, break_on_hyphens=False))

def save_pdf(title: str, layout: list[ComicLayoutItem]) -> str:
    filename=f"comic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    path=EXPORT_DIR/filename
    pdf=FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)
    for panel in layout:
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_x(15)
        pdf.multi_cell(180, 10, f"Panel {panel.panel_number}: {panel.title}")
        image_path=_local_image_path(panel.image_path)
        if image_path.exists():
            pdf.image(str(image_path), x=15, y=38, w=180, h=105)
            pdf.set_y(150)
        else:
            pdf.set_y(45)
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_x(15)
        pdf.multi_cell(180, 6, _pdf_text(panel.scene_description).encode("latin-1", "replace").decode("latin-1"))
        pdf.ln(3)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_x(15)
        pdf.multi_cell(180, 7, "Caption")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_x(15)
        pdf.multi_cell(180, 6, _pdf_text(panel.caption).encode("latin-1", "replace").decode("latin-1"))
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_x(15)
        pdf.multi_cell(180, 7, "Narration")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_x(15)
        pdf.multi_cell(180, 6, _pdf_text(panel.narration).encode("latin-1", "replace").decode("latin-1"))
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 11)
        pdf.set_x(15)
        pdf.multi_cell(180, 7, "Dialogue")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_x(15)
        pdf.multi_cell(180, 6, _pdf_text(panel.dialogue).encode("latin-1", "replace").decode("latin-1"))
    pdf.output(str(path))
    return f"/static/exports/{filename}"
