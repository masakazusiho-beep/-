"""動画の組み立て: テロップ画像(Pillow) + 音声 を ffmpeg で MP4 にする."""

from __future__ import annotations

import pathlib
import subprocess
from typing import List

from .config import TikTokConfig

# CI（Ubuntu）に入れる Noto CJK を優先。Mac のヒラギノもフォールバックに含める。
_FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Bold.otf",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc",
]


def find_font(cfg: TikTokConfig) -> str:
    if cfg.font_path and pathlib.Path(cfg.font_path).exists():
        return cfg.font_path
    for path in _FONT_CANDIDATES:
        if pathlib.Path(path).exists():
            return path
    raise RuntimeError(
        "日本語フォントが見つかりません。CI では fonts-noto-cjk を入れるか、"
        "config の font_path を指定してください。"
    )


def wrap_text(text: str, max_chars: int) -> List[str]:
    """日本語向けに、最大文字数で折り返した行のリストを返す（純ロジック）."""
    max_chars = max(1, max_chars)
    lines: List[str] = []
    for paragraph in text.splitlines() or [text]:
        if not paragraph:
            lines.append("")
            continue
        for i in range(0, len(paragraph), max_chars):
            lines.append(paragraph[i : i + max_chars])
    return lines or [""]


def make_frame(text: str, out_path: str | pathlib.Path, cfg: TikTokConfig) -> pathlib.Path:
    """テロップ1枚の PNG を作る."""
    from PIL import Image, ImageDraw, ImageFont

    out_path = pathlib.Path(out_path)
    img = Image.new("RGB", (cfg.width, cfg.height), cfg.bg_color)
    draw = ImageDraw.Draw(img)

    # 文字数に応じてフォントサイズを決める（短いほど大きく）
    font_size = 96 if len(text) <= 16 else 72 if len(text) <= 28 else 56
    font = ImageFont.truetype(find_font(cfg), font_size)

    max_chars = max(1, int((cfg.width * 0.82) / font_size))
    lines = wrap_text(text, max_chars)

    line_h = int(font_size * 1.4)
    total_h = line_h * len(lines)
    y = (cfg.height - total_h) // 2
    for line in lines:
        w = draw.textlength(line, font=font)
        draw.text(((cfg.width - w) / 2, y), line, fill=cfg.text_color, font=font)
        y += line_h

    img.save(out_path)
    return out_path


# 会話形式で使う、キャラごとの色（背景の丸）
_AVATAR_COLORS = ["#F59E0B", "#3B82F6"]

_EMOJI_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf",
    "/usr/share/fonts/google-noto-emoji/NotoColorEmoji.ttf",
    "/System/Library/Fonts/Apple Color Emoji.ttc",
]


def find_emoji_font() -> str | None:
    for path in _EMOJI_FONT_CANDIDATES:
        if pathlib.Path(path).exists():
            return path
    return None


def _emoji_image(emoji: str, size: int):
    """絵文字を size×size の RGBA 画像にする。失敗したら None。"""
    from PIL import Image, ImageDraw, ImageFont

    font_path = find_emoji_font()
    if not font_path or not emoji:
        return None
    try:
        font = ImageFont.truetype(font_path, 109)  # Noto Color Emoji の標準サイズ
        canvas = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
        draw = ImageDraw.Draw(canvas)
        draw.text((80, 80), emoji, font=font, anchor="mm", embedded_color=True)
        bbox = canvas.getbbox()
        if bbox:
            canvas = canvas.crop(bbox)
        return canvas.resize((size, size))
    except Exception:
        return None


def _draw_avatar(img, draw, center, radius, character, color, highlighted, cfg):
    """色付きの丸＋絵文字（無理ならイニシャル）でキャラを描く。"""
    from PIL import ImageFont

    cx, cy = center
    # 影をつけて立体感
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)
    emoji_img = _emoji_image(character.emoji, int(radius * 1.3))
    if emoji_img is not None:
        img.paste(emoji_img, (int(cx - emoji_img.width / 2), int(cy - emoji_img.height / 2)), emoji_img)
    else:
        font = ImageFont.truetype(find_font(cfg), int(radius * 0.9))
        ch = (character.name or "?")[0]
        draw.text((cx, cy), ch, font=font, fill="#FFFFFF", anchor="mm")

    # 名前ラベル
    name_font = ImageFont.truetype(find_font(cfg), 40)
    draw.text((cx, cy + radius + 36), character.name, font=name_font,
              fill=cfg.text_color, anchor="mm")


def make_dialogue_frame(turn, script, out_path: str | pathlib.Path, cfg: TikTokConfig) -> pathlib.Path:
    """会話形式の1コマ（2キャラ＋吹き出し）を描く。"""
    from PIL import Image, ImageDraw, ImageFont

    out_path = pathlib.Path(out_path)
    img = Image.new("RGB", (cfg.width, cfg.height), cfg.bg_color)
    draw = ImageDraw.Draw(img)

    # タイトル（上部）
    title_font = ImageFont.truetype(find_font(cfg), 46)
    for j, line in enumerate(wrap_text(script.title, 18)[:2]):
        w = draw.textlength(line, font=title_font)
        draw.text(((cfg.width - w) / 2, 90 + j * 60), line, font=title_font, fill=cfg.text_color)

    # 2キャラ（話している方を大きく・明るく）
    positions = [(int(cfg.width * 0.28), 560), (int(cfg.width * 0.72), 560)]
    for idx, character in enumerate(script.characters[:2]):
        speaking = idx == turn.speaker
        radius = 150 if speaking else 110
        color = _AVATAR_COLORS[idx % len(_AVATAR_COLORS)]
        if not speaking:
            color = "#4B5563"  # 話していない方はグレーで控えめに
        _draw_avatar(img, draw, positions[idx], radius, character, color, speaking, cfg)

    # 吹き出し（中央〜下）
    bubble = [70, 920, cfg.width - 70, 1640]
    draw.rounded_rectangle(bubble, radius=48, fill="#FFFFFF")
    # しっぽ（話者の側へ）
    tail_x = positions[turn.speaker][0]
    draw.polygon([(tail_x - 40, 920), (tail_x + 40, 920), (tail_x, 850)], fill="#FFFFFF")

    line_font_size = 64 if len(turn.line) <= 28 else 52
    line_font = ImageFont.truetype(find_font(cfg), line_font_size)
    max_chars = max(1, int((bubble[2] - bubble[0] - 80) / line_font_size))
    lines = wrap_text(turn.line, max_chars)
    line_h = int(line_font_size * 1.45)
    y = (bubble[1] + bubble[3]) // 2 - (line_h * len(lines)) // 2
    for line in lines:
        w = draw.textlength(line, font=line_font)
        draw.text(((cfg.width - w) / 2, y), line, font=line_font, fill="#111827")
        y += line_h

    img.save(out_path)
    return out_path


def scene_clip(frame_png: str | pathlib.Path, audio_mp3: str | pathlib.Path,
               out_mp4: str | pathlib.Path) -> pathlib.Path:
    """静止画 + 音声 から 1 シーンの MP4 を作る（音声の長さに合わせる）."""
    out_mp4 = pathlib.Path(out_mp4)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(frame_png),
            "-i", str(audio_mp3),
            "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(out_mp4),
        ],
        check=True, capture_output=True,
    )
    return out_mp4


def concat(clip_paths: List[pathlib.Path], out_mp4: str | pathlib.Path,
           work_dir: str | pathlib.Path) -> pathlib.Path:
    """複数シーンの MP4 を結合して 1 本にする."""
    out_mp4 = pathlib.Path(out_mp4)
    work_dir = pathlib.Path(work_dir)
    list_file = work_dir / "concat.txt"
    list_file.write_text(
        "".join(f"file '{p.resolve()}'\n" for p in clip_paths), encoding="utf-8"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(list_file), "-c", "copy", str(out_mp4),
        ],
        check=True, capture_output=True,
    )
    return out_mp4
