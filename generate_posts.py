from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import pandas as pd
    from PIL import Image, ImageChops, ImageDraw, ImageFont
except ModuleNotFoundError as exc:
    missing = exc.name or "a required package"
    print(
        f"Missing dependency: {missing}\n"
        "Install the project requirements first:\n"
        "  python3 -m venv .venv\n"
        "  source .venv/bin/activate\n"
        "  pip install -r requirements.txt",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "speakers.csv"
PHOTOS = ROOT / "photos"
ASSETS = ROOT / "assets"
FONTS = ASSETS / "fonts"
OUTPUT = ROOT / "output"

BASE_CANVAS_SIZE = 1200
WHITE = "#ffffff"
BLACK = "#000405"
BLUE = "#003962"
BLUE_DARK = "#002235"
BLUE_DEEP = "#00131c"

DEFAULT_EVENT_NAME = "Silicon Valley Minerals Forum 2026"
DEFAULT_DATE = "16-17, June, 2026"
DEFAULT_LOCATION_LINE_1 = "Stanford | Doerr"
DEFAULT_LOCATION_LINE_2 = "School of Sustainability"


FONT_STYLES = {
    "regular": ("Aleo[wght].ttf", 400),
    "medium": ("Aleo[wght].ttf", 500),
    "bold": ("Aleo[wght].ttf", 700),
    "extra_bold": ("Aleo[wght].ttf", 800),
    "italic": ("Aleo-Italic[wght].ttf", 400),
    "bold_italic": ("Aleo-Italic[wght].ttf", 700),
}


def load_font(kind: str, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load an Aleo font variant at the requested pixel size."""
    filename, weight = FONT_STYLES[kind]
    path = FONTS / filename
    if not path.exists():
        fallback = "/System/Library/Fonts/Supplemental/Georgia.ttf"
        if Path(fallback).exists():
            return ImageFont.truetype(fallback, size=size)
        return ImageFont.load_default(size=size)

    font = ImageFont.truetype(path, size=size)
    if hasattr(font, "set_variation_by_axes"):
        font.set_variation_by_axes([weight])
    return font


def scale_value(value: int | float, scale: float) -> int:
    """Scale a single numeric design coordinate from the base canvas."""
    return round(value * scale)


def scale_point(point: tuple[int, int], scale: float) -> tuple[int, int]:
    """Scale an ``(x, y)`` point from the base canvas."""
    return scale_value(point[0], scale), scale_value(point[1], scale)


def scale_bounds(bounds: tuple[int, int, int, int], scale: float) -> tuple[int, int, int, int]:
    """Scale a bounding box from the base canvas."""
    return tuple(scale_value(value, scale) for value in bounds)


def scale_size(size: tuple[int, int], scale: float) -> tuple[int, int]:
    """Scale a ``(width, height)`` size from the base canvas."""
    return scale_value(size[0], scale), scale_value(size[1], scale)


def text_size(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> tuple[int, int]:
    """Return rendered text width and height for a Pillow font."""
    if not text:
        return 0, 0
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    kind: str,
    start_size: int,
    max_width: int,
    min_size: int = 18,
) -> ImageFont.ImageFont:
    """Reduce a font size until text fits within ``max_width``."""
    size = start_size
    while size > min_size:
        font = load_font(kind, size)
        width, _ = text_size(draw, text, font)
        if width <= max_width:
            return font
        size -= 1
    return load_font(kind, min_size)


def draw_right_aligned_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    right_x: int,
    y: int,
    font: ImageFont.ImageFont,
    fill: str = WHITE,
) -> None:
    """Draw one line of text with its right edge fixed at ``right_x``."""
    text_width, _ = text_size(draw, text, font)
    draw.text((right_x - text_width, y), text, font=font, fill=fill)


def draw_text_at_visible_top(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: str = WHITE,
) -> None:
    """Draw text so the visible ink begins at the requested top-left point."""
    left, top, _, _ = draw.textbbox((0, 0), text, font=font)
    x, y = xy
    draw.text((x - left, y - top), text, font=font, fill=fill)


def trim_logo(image: Image.Image, threshold: int = 12) -> Image.Image:
    """Crop transparent or near-black padding from an asset image."""
    rgba = image.convert("RGBA")
    alpha_box = rgba.getchannel("A").getbbox()
    if alpha_box and alpha_box != (0, 0, rgba.width, rgba.height):
        return rgba.crop(alpha_box)

    from PIL import ImageChops

    background = Image.new("RGB", rgba.size, (0, 0, 0))
    difference = ImageChops.difference(rgba.convert("RGB"), background)
    content_box = difference.convert("L").point(lambda value: 255 if value > threshold else 0).getbbox()
    if content_box:
        return rgba.crop(content_box)
    return rgba


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    width: int,
    font: ImageFont.ImageFont,
    fill: str = WHITE,
) -> None:
    """Draw one line of text centered in a fixed-width region."""
    text_width, _ = text_size(draw, text, font)
    draw.text((x + (width - text_width) / 2, y), text, font=font, fill=fill)


def draw_right_aligned_multiline(
    draw: ImageDraw.ImageDraw,
    text: str,
    right_x: int,
    y: int,
    font: ImageFont.ImageFont,
    line_gap: int,
    fill: str = WHITE,
) -> None:
    """Draw multiline text with all lines right-aligned to the same x position."""
    for line in str(text).splitlines():
        draw_right_aligned_text(draw, line, right_x, y, font, fill)
        _, height = text_size(draw, line, font)
        y += height + line_gap


def rgba(color: str, alpha: int) -> tuple[int, int, int, int]:
    """Convert a hex color and alpha value to an RGBA tuple."""
    color = color.lstrip("#")
    return tuple(int(color[index : index + 2], 16) for index in (0, 2, 4)) + (alpha,)


def interpolate_rgba(
    left: tuple[int, int, int, int],
    right: tuple[int, int, int, int],
    amount: float,
) -> tuple[int, int, int, int]:
    """Linearly interpolate between two RGBA colors."""
    return tuple(round(left[index] + (right[index] - left[index]) * amount) for index in range(4))


def draw_gradient_circle(
    canvas: Image.Image,
    bounds: tuple[int, int, int, int],
    left_rgba: tuple[int, int, int, int],
    right_rgba: tuple[int, int, int, int],
) -> None:
    """Draw an ellipse mask filled with a horizontal RGBA gradient."""
    left, top, right, bottom = bounds
    width = right - left
    height = bottom - top
    if width <= 0 or height <= 0:
        return

    gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(gradient)
    for x in range(width):
        amount = x / (width - 1) if width > 1 else 1
        gradient_draw.line((x, 0, x, height), fill=interpolate_rgba(left_rgba, right_rgba, amount))

    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, width, height), fill=255)
    gradient_alpha = ImageChops.multiply(gradient.getchannel("A"), mask)
    gradient.putalpha(gradient_alpha)

    visible_left = max(0, -left)
    visible_top = max(0, -top)
    visible_right = min(width, canvas.width - left)
    visible_bottom = min(height, canvas.height - top)
    if visible_right <= visible_left or visible_bottom <= visible_top:
        return

    cropped = gradient.crop((visible_left, visible_top, visible_right, visible_bottom))
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    overlay.alpha_composite(cropped, (left + visible_left, top + visible_top))
    canvas.alpha_composite(overlay)


def draw_background(canvas: Image.Image, scale: float) -> None:
    """Draw the fixed circular gradient background."""
    draw = ImageDraw.Draw(canvas)
    transparent_black = (0, 0, 0, 0)
    gradient_blue = rgba(BLUE, 255)

    # Top row: circles fade from transparent black on the left to blue on the right.
    draw_gradient_circle(canvas, scale_bounds((501, -123, 1036, 412), scale), transparent_black, gradient_blue)
    draw_gradient_circle(canvas, scale_bounds((768, -123, 1303, 412), scale), transparent_black, gradient_blue)

    # Bottom row: reverse direction, blue on the left fading to transparent black.
    draw_gradient_circle(canvas, scale_bounds((-85, 719, 422, 1226), scale), gradient_blue, transparent_black)
    draw_gradient_circle(canvas, scale_bounds((179, 719, 714, 1254), scale), gradient_blue, transparent_black)

    # Large anchors follow the same gradient direction as the smaller circles
    # in their rows.
    draw_gradient_circle(canvas, scale_bounds((-238, -226, 698, 710), scale), transparent_black, gradient_blue)
    draw_gradient_circle(canvas, scale_bounds((502, 486, 1384, 1368), scale), gradient_blue, transparent_black)



def center_crop_square(image: Image.Image) -> Image.Image:
    """Center-crop an image to the largest possible square."""
    width, height = image.size
    side = min(width, height)
    left = (width - side) // 2
    top = (height - side) // 2
    return image.crop((left, top, left + side, top + side))


def paste_circle_photo(
    canvas: Image.Image,
    photo_path: Path,
    xy: tuple[int, int],
    size: int,
) -> None:
    """Crop, resize, and paste a speaker photo through a circular mask."""
    photo = Image.open(photo_path).convert("RGB")
    photo = center_crop_square(photo).resize((size, size), Image.Resampling.LANCZOS)

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size, size), fill=255)
    canvas.paste(photo, xy, mask)


def paste_logo(
    canvas: Image.Image,
    logo_path: Path,
    xy: tuple[int, int],
    max_size: tuple[int, int],
) -> None:
    """Paste a trimmed logo into a bounded region while preserving aspect ratio."""
    if not logo_path.exists():
        return
    logo = trim_logo(Image.open(logo_path))
    logo.thumbnail(max_size, Image.Resampling.LANCZOS)
    canvas.paste(logo, xy, logo)


def draw_footer(canvas: Image.Image, draw: ImageDraw.ImageDraw, row: pd.Series, scale: float) -> None:
    """Draw the fixed event date and location footer."""
    date = str(row.get("date", DEFAULT_DATE))
    line_1 = str(row.get("location_line_1", DEFAULT_LOCATION_LINE_1))
    line_2 = str(row.get("location_line_2", DEFAULT_LOCATION_LINE_2))

    draw.text(scale_point((36, 1019), scale), date, font=load_font("regular", scale_value(35, scale)), fill=WHITE)

    y = scale_value(1072, scale)
    font_bold = load_font("bold", scale_value(43, scale))
    font_regular = load_font("regular", scale_value(43, scale))
    x = scale_value(36, scale)

    if "|" in line_1:
        left, right = [part.strip() for part in line_1.split("|", 1)]
        draw.text((x, y), left, font=font_bold, fill=WHITE)
        left_width, _ = text_size(draw, left, font_bold)
        divider = " | "
        draw.text((x + left_width, y), divider, font=font_regular, fill=WHITE)
        divider_width, _ = text_size(draw, divider, font_regular)
        draw.text((x + left_width + divider_width, y), right, font=font_regular, fill=WHITE)
    else:
        draw.text((x, y), line_1, font=font_regular, fill=WHITE)

    draw.text(scale_point((36, 1129), scale), line_2, font=load_font("regular", scale_value(31, scale)), fill=WHITE)


def draw_post(
    row: pd.Series,
    photos_dir: Path,
    assets_dir: Path,
    output_size: int = BASE_CANVAS_SIZE,
) -> Image.Image:
    """Render one speaker poster from a CSV row."""
    scale = output_size / BASE_CANVAS_SIZE
    image = Image.new("RGBA", (output_size, output_size), BLACK)
    draw = ImageDraw.Draw(image)

    draw_background(image, scale)
    paste_logo(
        image,
        assets_dir / "MINERAL_X_LOGO_DARK_BACKGROUND_ALLPNG.png",
        scale_point((990, 55), scale),
        scale_size((151, 107), scale),
    )

    headline_font = load_font("regular", scale_value(126, scale))
    headline_speaker_font = load_font("extra_bold", scale_value(128, scale))
    draw_text_at_visible_top(draw, scale_point((61, 116), scale), "Meet", font=headline_font, fill=WHITE)
    draw_text_at_visible_top(draw, scale_point((61, 268), scale), "our", font=headline_font, fill=WHITE)
    draw_text_at_visible_top(draw, scale_point((61, 379), scale), "Speaker", font=headline_speaker_font, fill=WHITE)

    event_title = str(row.get("event_name", DEFAULT_EVENT_NAME))
    if event_title == "Silicon Valley Minerals Forum 2026":
        event_title = "Silicon Valley\nMinerals Forum 2026"
    else:
        event_title = event_title.replace(" Minerals ", " Minerals\n", 1)
    draw_right_aligned_multiline(
        draw,
        event_title,
        right_x=scale_value(1138, scale),
        y=scale_value(177, scale),
        font=load_font("regular", scale_value(34, scale)),
        line_gap=scale_value(-1, scale),
    )

    draw_gradient_circle(image, scale_bounds((586, 413, 1116, 943), scale), (0, 0, 0, 0), rgba(BLUE, 255))
    photo_path = photos_dir / str(row["photo_filename"])
    paste_circle_photo(image, photo_path, scale_point((631, 459), scale), scale_value(439, scale))

    name_font = fit_font(
        draw,
        str(row["speaker_name"]),
        "extra_bold",
        scale_value(55, scale),
        scale_value(500, scale),
        scale_value(18, scale),
    )
    title_font = fit_font(
        draw,
        str(row["title"]),
        "regular",
        scale_value(39, scale),
        scale_value(500, scale),
        scale_value(18, scale),
    )
    org_font = fit_font(
        draw,
        str(row["organization"]),
        "regular",
        scale_value(31, scale),
        scale_value(500, scale),
        scale_value(18, scale),
    )

    draw_centered_text(
        draw,
        str(row["speaker_name"]),
        scale_value(608, scale),
        scale_value(957, scale),
        scale_value(500, scale),
        name_font,
    )
    draw_centered_text(
        draw,
        str(row["title"]),
        scale_value(608, scale),
        scale_value(1036, scale),
        scale_value(500, scale),
        title_font,
    )
    draw_centered_text(
        draw,
        str(row["organization"]),
        scale_value(608, scale),
        scale_value(1091, scale),
        scale_value(500, scale),
        org_font,
    )

    draw_footer(image, draw, row, scale)
    return image


def generate_posts(
    csv_path: Path,
    photos_dir: Path,
    assets_dir: Path,
    output_dir: Path,
    output_size: int = BASE_CANVAS_SIZE,
) -> None:
    """Generate one PNG poster for every row with an available photo."""
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(csv_path, encoding="utf-8-sig").fillna("")
    df.columns = [column.strip().lstrip("\ufeff") for column in df.columns]

    required_columns = {
        "speaker_name",
        "title",
        "organization",
        "photo_filename",
        "output_filename",
    }
    missing_columns = sorted(required_columns - set(df.columns))
    if missing_columns:
        raise ValueError(f"Missing CSV columns: {', '.join(missing_columns)}")

    saved_count = 0
    skipped_count = 0
    for _, row in df.iterrows():
        photo_path = photos_dir / str(row["photo_filename"])
        if not photo_path.exists():
            skipped_count += 1
            print(f"Skipped {row['speaker_name']}: photo not found at {photo_path}", file=sys.stderr)
            continue

        output_path = output_dir / str(row["output_filename"])
        post = draw_post(row, photos_dir, assets_dir, output_size)
        post.convert("RGB").save(output_path)
        saved_count += 1
        print(f"Saved {output_path}")

    print(f"Done. Saved {saved_count} post(s); skipped {skipped_count} row(s) with missing photos.")


def parse_args() -> argparse.Namespace:
    """Parse command-line options for batch poster generation."""
    parser = argparse.ArgumentParser(description="Generate SVMF LinkedIn speaker posts.")
    parser.add_argument("--csv", type=Path, default=DATA, help="Path to speakers CSV.")
    parser.add_argument("--photos", type=Path, default=PHOTOS, help="Directory containing speaker photos.")
    parser.add_argument("--assets", type=Path, default=ASSETS, help="Directory containing fixed design assets.")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="Directory for generated PNG files.")
    parser.add_argument("--size", type=int, default=BASE_CANVAS_SIZE, help="Output width/height in pixels.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    generate_posts(args.csv, args.photos, args.assets, args.output, args.size)
