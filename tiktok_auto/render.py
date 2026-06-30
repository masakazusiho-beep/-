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
