from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "beamer_to_keynote.py"
SPEC = importlib.util.spec_from_file_location("beamer_to_keynote", MODULE_PATH)
assert SPEC is not None
beamer_to_keynote = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = beamer_to_keynote
SPEC.loader.exec_module(beamer_to_keynote)


def test_parse_beamer_slide_with_bullets_math_and_image(tmp_path: Path):
    image_path = tmp_path / "figure.png"
    image_path.write_bytes(b"placeholder")
    source = r"""
\documentclass{beamer}
\begin{document}
\begin{frame}{Bayes update}
\begin{itemize}
  \item Prior belief
  \item Evidence likelihood
\end{itemize}
\[
P(H \mid E) = \frac{P(E \mid H)P(H)}{P(E)}
\]
\includegraphics[width=0.5\textwidth]{figure.png}
\end{frame}
\end{document}
"""

    slide = beamer_to_keynote.parse_beamer_slide(source, base_dir=tmp_path)

    assert slide.title == "Bayes update"
    assert [element.kind for element in slide.elements] == ["bullets", "math", "image"]
    assert slide.elements[0].value == "- Prior belief\n- Evidence likelihood"
    assert "P(H \\mid E)" in slide.elements[1].value
    assert slide.elements[2].value == image_path.resolve()
    assert slide.elements[2].width_fraction == 0.5


def test_parse_beamer_slides_reads_every_frame(tmp_path: Path):
    source = r"""
\documentclass{beamer}
\begin{document}
\begin{frame}{First}
Intro text.
\end{frame}
\begin{frame}
\frametitle{Second}
\begin{itemize}
  \item One
  \item Two
\end{itemize}
\end{frame}
\end{document}
"""

    slides = beamer_to_keynote.parse_beamer_slides(source, base_dir=tmp_path)

    assert len(slides) == 2
    assert slides[0].title == "First"
    assert slides[0].elements[0].value == "Intro text."
    assert slides[1].title == "Second"
    assert slides[1].elements[0].value == "- One\n- Two"


def test_parse_beamer_slide_preserves_align_environment(tmp_path: Path):
    source = r"""
\documentclass{beamer}
\begin{document}
\begin{frame}{Aligned}
\begin{align*}
  A &\rightarrow B\\
  B &\rightarrow C
\end{align*}
\end{frame}
\end{document}
"""

    slide = beamer_to_keynote.parse_beamer_slide(source, base_dir=tmp_path)

    assert slide.elements[0].kind == "math"
    assert slide.elements[0].value.startswith(r"\begin{align*}")
    assert slide.elements[0].value.endswith(r"\end{align*}")


def test_parse_markdown_slide(tmp_path: Path):
    source = """
# Search frontier

- push start
- pop lowest cost

$$
f(n) = g(n) + h(n)
$$

![frontier](frontier.pdf)
"""

    slide = beamer_to_keynote.parse_markdown_slide(source, base_dir=tmp_path)

    assert slide.title == "Search frontier"
    assert [element.kind for element in slide.elements] == ["bullets", "math", "image"]
    assert slide.elements[0].value == "- push start\n- pop lowest cost"
    assert slide.elements[1].value == "f(n) = g(n) + h(n)"
    assert slide.elements[2].value == (tmp_path / "frontier.pdf").resolve()


def test_parse_markdown_slides_split_on_horizontal_rule(tmp_path: Path):
    slides = beamer_to_keynote.parse_markdown_slides(
        """
# One
Body one

---

# Two
Body two
""",
        base_dir=tmp_path,
    )

    assert [slide.title for slide in slides] == ["One", "Two"]
    assert [slide.elements[0].value for slide in slides] == ["Body one", "Body two"]


def test_build_keynote_applescript_escapes_text_and_paths(tmp_path: Path):
    slide = beamer_to_keynote.SlideSpec(
        title="ignored",
        elements=(),
        base_dir=tmp_path,
    )
    placed = (
        beamer_to_keynote.PlacedElement(
            "title",
            'A "quoted" title',
            100,
            70,
            1200,
            90,
            46,
        ),
        beamer_to_keynote.PlacedElement(
            "image",
            tmp_path / 'figure "one".pdf',
            200,
            200,
            600,
            300,
        ),
    )

    script = beamer_to_keynote.build_keynote_applescript(
        slide,
        placed,
        tmp_path / "out.key",
    )

    assert 'object text:"A \\"quoted\\" title"' in script
    assert 'file:POSIX file "' in script
    assert "set position of slide1item2" in script
    assert '\\"one\\".pdf' in script
    assert "save in POSIX file" in script


def test_build_keynote_deck_applescript_adds_subsequent_slides(tmp_path: Path):
    slides = (
        beamer_to_keynote.SlideSpec("One", (), tmp_path),
        beamer_to_keynote.SlideSpec("Two", (), tmp_path),
    )
    placed = (
        (beamer_to_keynote.PlacedElement("title", "One", 0, 0, 100, 50, 24),),
        (beamer_to_keynote.PlacedElement("title", "Two", 0, 0, 100, 50, 24),),
    )

    script = beamer_to_keynote.build_keynote_deck_applescript(
        slides,
        placed,
        tmp_path / "out.key",
    )

    assert "set s to slide 1" in script
    assert 'make new slide at end of slides' in script
    assert 'object text:"One"' in script
    assert 'object text:"Two"' in script


def test_parse_pdf_slide_uses_pdf_dimensions(tmp_path: Path, monkeypatch):
    pdf_path = tmp_path / "slide.pdf"
    pdf_path.write_bytes(b"%PDF-placeholder")
    monkeypatch.setattr(beamer_to_keynote, "_measure_asset", lambda path: (842.0, 595.0))

    slide = beamer_to_keynote.parse_pdf_slide(pdf_path)
    placed = beamer_to_keynote.layout_slide(slide)
    script = beamer_to_keynote.build_keynote_applescript(slide, placed, tmp_path / "out.key")

    assert slide.width == 842
    assert slide.height == 595
    assert slide.full_page is True
    assert placed[0].width == 842
    assert placed[0].height == 595
    assert "width:842, height:595" in script


def test_array_math_is_wrapped_in_display_math(tmp_path: Path, monkeypatch):
    written: dict[str, str] = {}

    def fake_write_text(self, text, *args, **kwargs):
        written["text"] = text
        return len(text)

    def fake_run(*args, **kwargs):
        return beamer_to_keynote.subprocess.CompletedProcess(args[0], 0, "")

    monkeypatch.setattr(Path, "write_text", fake_write_text)
    monkeypatch.setattr(beamer_to_keynote.subprocess, "run", fake_run)

    beamer_to_keynote._render_math_pdf(
        r"\begin{array}{rcl}K &: \text{key}\\ L &: \text{locked}\end{array}",
        tmp_path,
        1,
    )

    assert r"\[" in written["text"]
    assert r"\begin{array}" in written["text"]
    assert r"\newcommand{\model}" in written["text"]
