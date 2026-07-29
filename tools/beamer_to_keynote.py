#!/usr/bin/env python3
"""Create a Keynote deck from simple Beamer, Markdown, or PDF input.

This deliberately avoids writing Keynote's private ``Index/*.iwa`` records
directly. A modern ``.key`` file is a zip archive with private iWork archives,
assets, metadata, and previews; Keynote is used here as the writer while this
tool owns parsing, layout, and LaTeX maths rendering.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


SLIDE_WIDTH = 1920
SLIDE_HEIGHT = 1080
CONTENT_LEFT = 135
CONTENT_TOP = 185
CONTENT_WIDTH = 1650
CONTENT_BOTTOM = 1010


@dataclass(frozen=True)
class SlideElement:
    """One high-level element in the source slide."""

    kind: str
    value: str | Path
    width_fraction: float | None = None


@dataclass(frozen=True)
class SlideSpec:
    """A normalised single-slide representation."""

    title: str
    elements: tuple[SlideElement, ...]
    base_dir: Path
    width: int = SLIDE_WIDTH
    height: int = SLIDE_HEIGHT
    full_page: bool = False


@dataclass(frozen=True)
class PlacedElement:
    """One positioned element to emit into Keynote."""

    kind: str
    value: str | Path
    x: int
    y: int
    width: int
    height: int
    font_size: int | None = None


def parse_slide(source: str, *, base_dir: Path, source_format: str = "auto") -> SlideSpec:
    """Parse a single Beamer frame or Markdown slide."""

    return parse_slides(source, base_dir=base_dir, source_format=source_format)[0]


def parse_slides(
    source: str, *, base_dir: Path, source_format: str = "auto"
) -> tuple[SlideSpec, ...]:
    """Parse one or more Beamer or Markdown slides."""

    if source_format == "auto":
        source_format = "markdown" if _looks_like_markdown(source) else "beamer"
    if source_format == "markdown":
        return parse_markdown_slides(source, base_dir=base_dir)
    if source_format == "beamer":
        return parse_beamer_slides(source, base_dir=base_dir)
    raise ValueError(f"Unsupported source format: {source_format}")


def load_slide(input_path: Path, *, source_format: str = "auto") -> SlideSpec:
    """Load one slide from a Beamer, Markdown, or PDF file."""

    return load_slides(input_path, source_format=source_format)[0]


def load_slides(input_path: Path, *, source_format: str = "auto") -> tuple[SlideSpec, ...]:
    """Load one or more slides from a Beamer, Markdown, or PDF file."""

    input_path = input_path.expanduser().resolve()
    if source_format == "auto" and input_path.suffix.lower() == ".pdf":
        source_format = "pdf"
    if source_format == "pdf":
        return (parse_pdf_slide(input_path),)

    source = input_path.read_text(encoding="utf-8")
    return parse_slides(source, base_dir=input_path.parent, source_format=source_format)


def parse_pdf_slide(input_path: Path) -> SlideSpec:
    """Represent one PDF page as a full-slide image."""

    width, height = _measure_asset(input_path)
    return SlideSpec(
        title="",
        elements=(SlideElement("image", input_path.resolve(), 1.0),),
        base_dir=input_path.parent,
        width=max(1, int(round(width))),
        height=max(1, int(round(height))),
        full_page=True,
    )


def parse_beamer_slide(source: str, *, base_dir: Path) -> SlideSpec:
    """Parse the first Beamer frame in ``source``."""

    return parse_beamer_slides(source, base_dir=base_dir)[0]


def parse_beamer_slides(source: str, *, base_dir: Path) -> tuple[SlideSpec, ...]:
    """Parse every Beamer frame in ``source``."""

    source = _strip_tex_comments(source)
    frames = _extract_frames(source)
    if not frames:
        raise ValueError("No Beamer frame found")

    slides: list[SlideSpec] = []
    for frame in frames:
        title = frame["title"] or ""
        body = frame["body"]

        if not title:
            title_match = re.search(r"\\frametitle\{([^{}]*)\}", body, flags=re.DOTALL)
            if title_match:
                title = _clean_tex_text(title_match.group(1))
                body = body[: title_match.start()] + body[title_match.end() :]

        elements = tuple(_parse_tex_elements(body, base_dir=base_dir))
        slides.append(SlideSpec(title=title or "Untitled", elements=elements, base_dir=base_dir))
    return tuple(slides)


def parse_markdown_slide(source: str, *, base_dir: Path) -> SlideSpec:
    """Parse a small Markdown slide with a title, bullets, maths, and images."""

    return parse_markdown_slides(source, base_dir=base_dir)[0]


def parse_markdown_slides(source: str, *, base_dir: Path) -> tuple[SlideSpec, ...]:
    """Parse Markdown slides split with horizontal-rule separators."""

    chunks = [
        chunk.strip()
        for chunk in re.split(r"(?m)^\s*---\s*$", source)
        if chunk.strip()
    ]
    if not chunks:
        chunks = [source]
    return tuple(_parse_markdown_slide(chunk, base_dir=base_dir) for chunk in chunks)


def _parse_markdown_slide(source: str, *, base_dir: Path) -> SlideSpec:
    """Parse one small Markdown slide with a title, bullets, maths, and images."""

    lines = source.splitlines()
    title = "Untitled"
    elements: list[SlideElement] = []
    paragraph: list[str] = []
    i = 0

    def flush_paragraph() -> None:
        if paragraph:
            elements.append(SlideElement("text", " ".join(part.strip() for part in paragraph)))
            paragraph.clear()

    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()
        if not stripped:
            flush_paragraph()
            i += 1
            continue
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            i += 1
            continue
        if stripped.startswith("$$"):
            flush_paragraph()
            maths: list[str] = []
            first = stripped[2:].strip()
            if first:
                maths.append(first)
            i += 1
            while i < len(lines) and not lines[i].strip().endswith("$$"):
                maths.append(lines[i])
                i += 1
            if i < len(lines):
                closing = lines[i].strip()
                before_close = closing[:-2].strip()
                if before_close:
                    maths.append(before_close)
                i += 1
            elements.append(SlideElement("math", "\n".join(maths).strip()))
            continue
        image_match = re.match(r"!\[[^\]]*\]\(([^)]+)\)", stripped)
        if image_match:
            flush_paragraph()
            elements.append(SlideElement("image", _resolve_asset_path(image_match.group(1), base_dir)))
            i += 1
            continue
        if re.match(r"[-*]\s+", stripped):
            flush_paragraph()
            items = []
            while i < len(lines):
                item_match = re.match(r"\s*[-*]\s+(.+)", lines[i])
                if not item_match:
                    break
                items.append(item_match.group(1).strip())
                i += 1
            elements.append(SlideElement("bullets", "\n".join(f"- {item}" for item in items)))
            continue
        paragraph.append(stripped)
        i += 1

    flush_paragraph()
    return SlideSpec(title=title, elements=tuple(elements), base_dir=base_dir)


def create_keynote_deck(
    specs: SlideSpec | Sequence[SlideSpec], output_path: Path, *, keep_temp: bool = False
) -> Path:
    """Render assets, drive Keynote with AppleScript, and write ``output_path``."""

    if isinstance(specs, SlideSpec):
        slide_specs = (specs,)
    else:
        slide_specs = tuple(specs)
    if not slide_specs:
        raise ValueError("At least one slide is required")

    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        if output_path.is_dir():
            shutil.rmtree(output_path)
        else:
            output_path.unlink()

    with tempfile.TemporaryDirectory(prefix="beamer2keynote-") as temp_name:
        temp_dir = Path(temp_name)
        rendered_specs = render_deck_math_assets(slide_specs, temp_dir)
        placed = tuple(layout_slide(spec) for spec in rendered_specs)
        script = build_keynote_deck_applescript(rendered_specs, placed, output_path)
        subprocess.run(["osascript", "-e", script], check=True)
        if keep_temp:
            kept = output_path.with_suffix(output_path.suffix + ".assets")
            if kept.exists():
                shutil.rmtree(kept)
            shutil.copytree(temp_dir, kept)
    return output_path


def render_deck_math_assets(specs: Sequence[SlideSpec], temp_dir: Path) -> tuple[SlideSpec, ...]:
    """Render LaTeX maths elements for every slide in a deck."""

    rendered: list[SlideSpec] = []
    for index, spec in enumerate(specs, start=1):
        slide_dir = temp_dir / f"slide-{index}"
        slide_dir.mkdir(parents=True, exist_ok=True)
        rendered.append(render_math_assets(spec, slide_dir))
    return tuple(rendered)


def render_math_assets(spec: SlideSpec, temp_dir: Path) -> SlideSpec:
    """Render LaTeX maths elements as cropped PDF assets."""

    rendered: list[SlideElement] = []
    math_index = 1
    for element in spec.elements:
        if element.kind != "math":
            rendered.append(element)
            continue
        pdf_path = _render_math_pdf(str(element.value), temp_dir, math_index)
        rendered.append(SlideElement("math-image", pdf_path))
        math_index += 1
    return SlideSpec(
        title=spec.title,
        elements=tuple(rendered),
        base_dir=spec.base_dir,
        width=spec.width,
        height=spec.height,
        full_page=spec.full_page,
    )


def layout_slide(spec: SlideSpec) -> tuple[PlacedElement, ...]:
    """Lay out the one-slide intermediate representation on a 16:9 canvas."""

    if spec.full_page and len(spec.elements) == 1 and spec.elements[0].kind == "image":
        return (
            PlacedElement("image", Path(spec.elements[0].value), 0, 0, spec.width, spec.height),
        )

    placed: list[PlacedElement] = []
    if spec.title:
        placed.append(PlacedElement("title", spec.title, CONTENT_LEFT, 70, CONTENT_WIDTH, 90, 46))
    y = CONTENT_TOP if spec.title else 70
    remaining_elements = len(spec.elements)

    for element in spec.elements:
        remaining_elements -= 1
        if element.kind in {"text", "bullets"}:
            text = str(element.value)
            line_count = max(1, text.count("\n") + 1)
            height = max(74, line_count * 43 + 22)
            placed.append(
                PlacedElement(element.kind, text, CONTENT_LEFT, y, CONTENT_WIDTH, height, 31)
            )
            y += height + 26
            continue

        if element.kind in {"image", "math-image"}:
            natural_width, natural_height = _measure_asset(Path(element.value))
            width_fraction = element.width_fraction
            if width_fraction is None:
                width_fraction = 0.62 if element.kind == "image" else 0.48
            width = max(120, int(CONTENT_WIDTH * width_fraction))
            ratio = natural_height / natural_width if natural_width else 0.55
            height = max(70, int(width * ratio))
            max_height = max(120, CONTENT_BOTTOM - y - (remaining_elements * 90))
            if height > max_height:
                height = max_height
                width = max(120, int(height / ratio)) if ratio else width
            x = CONTENT_LEFT + max(0, (CONTENT_WIDTH - width) // 2)
            placed.append(PlacedElement("image", Path(element.value), x, y, width, height))
            y += height + 30

    return tuple(placed)


def build_keynote_applescript(
    spec: SlideSpec, elements: Sequence[PlacedElement], output_path: Path
) -> str:
    """Build the AppleScript used to create the Keynote document."""

    return build_keynote_deck_applescript((spec,), (tuple(elements),), output_path)


def build_keynote_deck_applescript(
    specs: Sequence[SlideSpec],
    placed_slides: Sequence[Sequence[PlacedElement]],
    output_path: Path,
) -> str:
    """Build the AppleScript used to create a multi-slide Keynote document."""

    if not specs:
        raise ValueError("At least one slide is required")
    if len(specs) != len(placed_slides):
        raise ValueError("Slide specs and placed slide lists must have the same length")

    lines = [
        'tell application "Keynote"',
        '  set doc to make new document with properties {document theme:theme "White", '
        + f"width:{specs[0].width}, height:{specs[0].height}"
        + "}",
        "  tell doc",
    ]

    for slide_index, elements in enumerate(placed_slides, start=1):
        if slide_index == 1:
            lines.append("    set s to slide 1")
        else:
            lines.append(
                '    set s to make new slide at end of slides with properties {base layout:slide layout "Blank"}'
            )
        lines.append('    set base layout of s to slide layout "Blank"')
        lines.append("    tell s")
        _append_keynote_slide_items(lines, tuple(elements), slide_index)
        lines.append("    end tell")

    lines.extend(
        [
            "    save in POSIX file " + _applescript_string(os.fspath(output_path)),
            "    close saving yes",
            "  end tell",
            "end tell",
        ]
    )
    return "\n".join(lines)


def _append_keynote_slide_items(
    lines: list[str], elements: Sequence[PlacedElement], slide_index: int
) -> None:
    for index, element in enumerate(elements, start=1):
        variable = f"slide{slide_index}item{index}"
        if element.kind in {"title", "text", "bullets"}:
            lines.append(
                "      set "
                + variable
                + " to make new text item with properties {object text:"
                + _applescript_string(str(element.value))
                + f", position:{{{element.x}, {element.y}}}, width:{element.width}, height:{element.height}}}"
            )
            if element.font_size is not None:
                lines.append(f"      set size of object text of {variable} to {element.font_size}")
        elif element.kind == "image":
            lines.append(
                "      set "
                + variable
                + " to make new image with properties {file:POSIX file "
                + _applescript_string(os.fspath(element.value))
                + "}"
            )
            lines.append(f"      set position of {variable} to {{{element.x}, {element.y}}}")
            lines.append(f"      set width of {variable} to {element.width}")
            lines.append(f"      set height of {variable} to {element.height}")


def _extract_frames(source: str) -> list[dict[str, str]]:
    frames: list[dict[str, str]] = []
    begin_pattern = re.compile(
        r"\\begin\{frame\}(?:\[[^\]]*\])?(?:\{(?P<title>[^{}]*)\})?",
        flags=re.DOTALL,
    )
    position = 0
    while True:
        begin = begin_pattern.search(source, position)
        if not begin:
            return frames
        end = re.search(r"\\end\{frame\}", source[begin.end() :], flags=re.DOTALL)
        if not end:
            raise ValueError("Frame is missing \\end{frame}")
        body_end = begin.end() + end.start()
        frames.append(
            {
                "title": _clean_tex_text(begin.group("title") or ""),
                "body": source[begin.end() : body_end],
            }
        )
        position = begin.end() + end.end()


def _parse_tex_elements(body: str, *, base_dir: Path) -> list[SlideElement]:
    token_pattern = re.compile(
        r"(?P<itemize>\\begin\{itemize\}.*?\\end\{itemize\})"
        r"|(?P<include>\\includegraphics(?:\[(?P<opts>[^\]]*)\])?\{(?P<path>[^{}]+)\})"
        r"|(?P<bracket>\\\[(?P<bracket_math>.*?)\\\])"
        r"|(?P<dollar>\$\$(?P<dollar_math>.*?)\$\$)"
        r"|(?P<equation>\\begin\{(?P<env>equation\*?|align\*?)\}(?P<env_math>.*?)\\end\{(?P=env)\})",
        flags=re.DOTALL,
    )
    elements: list[SlideElement] = []
    last_end = 0
    for match in token_pattern.finditer(body):
        _append_text_element(elements, body[last_end : match.start()])
        if match.group("itemize"):
            items = re.findall(
                r"\\item\s*(.*?)(?=(?:\\item\b|\\end\{itemize\}))",
                match.group("itemize"),
                flags=re.DOTALL,
            )
            cleaned = [_clean_tex_text(item) for item in items if _clean_tex_text(item)]
            if cleaned:
                elements.append(SlideElement("bullets", "\n".join(f"- {item}" for item in cleaned)))
        elif match.group("include"):
            width_fraction = _parse_width_fraction(match.group("opts") or "")
            elements.append(
                SlideElement(
                    "image",
                    _resolve_asset_path(match.group("path"), base_dir),
                    width_fraction,
                )
            )
        else:
            if match.group("env"):
                math = match.group("equation") or ""
            else:
                math = match.group("bracket_math") or match.group("dollar_math") or ""
            if math.strip():
                elements.append(SlideElement("math", math.strip()))
        last_end = match.end()

    _append_text_element(elements, body[last_end:])
    return elements


def _append_text_element(elements: list[SlideElement], raw_text: str) -> None:
    text = _clean_tex_text(raw_text)
    if text:
        elements.append(SlideElement("text", text))


def _render_math_pdf(math: str, temp_dir: Path, index: int) -> Path:
    tex_path = temp_dir / f"math-{index}.tex"
    body = math if _is_complete_display_math_environment(math) else "\\[\n" + math + "\n\\]"
    tex_path.write_text(
        "\n".join(
            [
                r"\documentclass[preview,border=4pt]{standalone}",
                r"\usepackage{amsmath,amssymb,mathtools}",
                r"\newcommand{\model}[1]{\{#1\}}",
                r"\begin{document}",
                body,
                r"\end{document}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", tex_path.name],
        cwd=temp_dir,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    pdf_path = temp_dir / f"math-{index}.pdf"
    if result.returncode != 0 and not pdf_path.exists():
        raise subprocess.CalledProcessError(
            result.returncode,
            result.args,
            output=result.stdout,
            stderr=result.stderr,
        )
    return pdf_path


def _is_complete_display_math_environment(math: str) -> bool:
    """Return true for environments that provide their own display maths mode."""

    match = re.match(r"\s*\\begin\{([^}]+)\}", math)
    if not match:
        return False
    environment = match.group(1).removesuffix("*")
    return environment in {
        "align",
        "alignat",
        "equation",
        "flalign",
        "gather",
        "multline",
    }


def _measure_asset(path: Path) -> tuple[float, float]:
    result = subprocess.run(
        ["sips", "-g", "pixelWidth", "-g", "pixelHeight", os.fspath(path)],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    width = height = 0.0
    for line in result.stdout.splitlines():
        if "pixelWidth:" in line:
            width = float(line.split(":", 1)[1].strip())
        if "pixelHeight:" in line:
            height = float(line.split(":", 1)[1].strip())
    if width <= 0 or height <= 0:
        return (800.0, 450.0)
    return (width, height)


def _strip_tex_comments(source: str) -> str:
    cleaned = []
    for line in source.splitlines():
        cleaned.append(re.sub(r"(?<!\\)%.*$", "", line))
    return "\n".join(cleaned)


def _clean_tex_text(text: str) -> str:
    text = re.sub(r"\\(?:textbf|textit|emph|alert)\{([^{}]*)\}", r"\1", text)
    text = re.sub(r"\\(?:pause|smallskip|medskip|bigskip)\b", "", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", "", text)
    text = text.replace(r"\%", "%").replace(r"\&", "&").replace(r"\_", "_")
    text = text.replace("$", "")
    text = re.sub(r"[{}]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_width_fraction(options: str) -> float | None:
    match = re.search(r"width\s*=\s*([0-9.]+)\s*\\(?:textwidth|linewidth)", options)
    if match:
        return max(0.1, min(float(match.group(1)), 1.0))
    return None


def _resolve_asset_path(raw_path: str, base_dir: Path) -> Path:
    raw_path = raw_path.strip()
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = base_dir / path
    if path.exists() or path.suffix:
        return path.resolve()
    for suffix in (".pdf", ".png", ".jpg", ".jpeg"):
        candidate = path.with_suffix(suffix)
        if candidate.exists():
            return candidate.resolve()
    return path.resolve()


def _looks_like_markdown(source: str) -> bool:
    return "\\begin{frame}" not in source and bool(
        re.search(r"(^#\s+)|(^[-*]\s+)|(!\[[^\]]*\]\()", source, flags=re.MULTILINE)
    )


def _applescript_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Translate simple Beamer, Markdown, or PDF input to a native Keynote deck.",
    )
    parser.add_argument("input", type=Path, help="Input .tex, Markdown, or PDF file.")
    parser.add_argument("output", type=Path, help="Output .key file.")
    parser.add_argument(
        "--format",
        choices=("auto", "beamer", "markdown", "pdf"),
        default="auto",
        help="Input format. Defaults to auto-detection.",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep rendered maths assets next to the output for inspection.",
    )
    parser.add_argument(
        "--print-applescript",
        action="store_true",
        help="Render maths assets and print the AppleScript instead of running Keynote.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    specs = load_slides(args.input, source_format=args.format)
    if args.print_applescript:
        asset_dir = args.output.resolve().with_suffix(args.output.suffix + ".assets")
        if asset_dir.exists():
            shutil.rmtree(asset_dir)
        asset_dir.mkdir(parents=True)
        rendered_specs = render_deck_math_assets(specs, asset_dir)
        placed = tuple(layout_slide(spec) for spec in rendered_specs)
        print(build_keynote_deck_applescript(rendered_specs, placed, args.output.resolve()))
        return 0
    try:
        create_keynote_deck(specs, args.output, keep_temp=args.keep_temp)
    except subprocess.CalledProcessError as exc:
        print(f"Error: external command failed: {exc.cmd}", file=sys.stderr)
        if exc.stdout:
            print(exc.stdout, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
