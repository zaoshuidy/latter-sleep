#!/usr/bin/env python3

from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont


CANVAS = (3650, 2551)
BACK_BOX = (35, 35, 1748, 2515)
SPINE_BOX = (1748, 35, 1902, 2515)
FRONT_BOX = (1902, 35, 3615, 2515)
FONT_PATH = "/System/Library/Fonts/Supplemental/Songti.ttc"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, size=size)


def draw_vertical(draw: ImageDraw.ImageDraw, text: str, center_x: int, top: int,
                  text_font: ImageFont.FreeTypeFont, fill: str,
                  step: int, accent_index: int | None = None,
                  accent_fill: str = "#a73720") -> None:
    for index, character in enumerate(text):
        bbox = draw.textbbox((0, 0), character, font=text_font)
        width = bbox[2] - bbox[0]
        color = accent_fill if index == accent_index else fill
        draw.text((center_x - width / 2, top + index * step), character,
                  font=text_font, fill=color)


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: render_lost_human_world_full_cover.py BACK.png FRONT.png OUTPUT.png", file=sys.stderr)
        return 2

    back_path, front_path, output_path = map(Path, sys.argv[1:])
    with Image.open(back_path) as back_source, Image.open(front_path) as front_source:
        back = back_source.convert("RGB").resize((1713, 2480), Image.Resampling.LANCZOS)
        front = front_source.convert("RGB").resize((1713, 2480), Image.Resampling.LANCZOS)

    canvas = Image.new("RGB", CANVAS, "#2d3436")
    canvas.paste(back, BACK_BOX[:2])

    # A restrained dark veil preserves the painting while creating a stable reading field.
    veil = Image.new("RGBA", back.size, (10, 16, 19, 46))
    back_rgba = back.convert("RGBA")
    back_rgba.alpha_composite(veil)
    canvas.paste(back_rgba.convert("RGB"), BACK_BOX[:2])

    draw = ImageDraw.Draw(canvas)
    draw.rectangle(SPINE_BOX, fill="#293134")
    draw.line((1748, 35, 1748, 2515), fill="#171d20", width=2)
    draw.line((1902, 35, 1902, 2515), fill="#171d20", width=2)
    canvas.paste(front, FRONT_BOX[:2])

    ivory = "#eee3ce"
    lead_font = font(42)
    copy_font = font(38)

    lead = ["人们用来路确认一个人，", "也用归处收留一个人。"]
    for index, line in enumerate(lead):
        draw.text((265, 410 + index * 70), line, font=lead_font, fill=ivory)

    middle = [
        "他曾相信远方会给予新的名字，", "后来才明白，", "城市只改变了他的生活，",
        "并没有替他找到位置。", "当旧日的灯一盏盏熄灭，", "故乡仍在，", "归来的人却成了异乡人。",
    ]
    for index, line in enumerate(middle):
        draw.text((265, 740 + index * 68), line, font=copy_font, fill=ivory)

    closing = ["有些离开通向抵达，", "有些归来只是另一种流落。", "在所有归途之外，", "他继续生活在人间。"]
    for index, line in enumerate(closing):
        draw.text((265, 1495 + index * 68), line, font=copy_font, fill=ivory)

    draw_vertical(draw, "失落人间", 1825, 475, font(43), ivory, 70,
                  accent_index=2, accent_fill="#a73720")
    draw_vertical(draw, "早睡的猫", 1825, 1605, font(28), ivory, 50)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, "PNG", dpi=(300, 300), optimize=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
