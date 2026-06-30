"""tiktok_auto の設定（note_config.toml を共有して読む）."""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore

DEFAULT_MODEL = "claude-opus-4-8"


@dataclass
class TikTokConfig:
    """ショート動画パイプラインの設定."""

    # --- コンテンツ（note と同じ [content] を流用）---
    theme: str = ""
    keywords: List[str] = field(default_factory=list)

    # --- 台本生成 ---
    model: str = DEFAULT_MODEL
    effort: str = "high"
    target_seconds: int = 30          # 動画のおおよその長さ

    # --- スタイル ---
    style: str = "plain"               # "plain"（テロップ）/ "dialogue"（会話形式）

    # --- 音声（無料の edge-tts）---
    voice: str = "ja-JP-NanamiNeural"  # キャラ0／ナレーション（女性）
    voice_b: str = "ja-JP-KeitaNeural"  # キャラ1（男性・会話形式で使用）
    speech_rate: str = "+0%"           # 例: "+10%" で少し速く

    # --- 見た目 ---
    width: int = 1080                 # 縦型 9:16
    height: int = 1920
    bg_color: str = "#111827"         # 背景色
    text_color: str = "#FFFFFF"
    font_path: Optional[str] = None   # 未指定なら自動探索（CI では Noto CJK）

    # --- 出力 ---
    output_dir: str = "videos"

    @classmethod
    def load(cls, path: Optional[str | pathlib.Path] = None) -> "TikTokConfig":
        data: dict = {}
        if path:
            p = pathlib.Path(path)
            if p.exists():
                if tomllib is None:  # pragma: no cover
                    raise RuntimeError("TOML 設定には Python 3.11+ が必要です")
                data = tomllib.loads(p.read_text(encoding="utf-8"))

        content = data.get("content", {})
        tk = data.get("tiktok", {})

        return cls(
            theme=content.get("theme", ""),
            keywords=list(content.get("keywords", [])),
            model=tk.get("model", DEFAULT_MODEL),
            effort=tk.get("effort", cls.effort),
            target_seconds=int(tk.get("target_seconds", cls.target_seconds)),
            style=tk.get("style", cls.style),
            voice=tk.get("voice", cls.voice),
            voice_b=tk.get("voice_b", cls.voice_b),
            speech_rate=tk.get("speech_rate", cls.speech_rate),
            bg_color=tk.get("bg_color", cls.bg_color),
            text_color=tk.get("text_color", cls.text_color),
            font_path=tk.get("font_path", None),
            output_dir=tk.get("output_dir", cls.output_dir),
        )
