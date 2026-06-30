"""動画台本のデータ構造."""

from __future__ import annotations

import datetime as _dt
import json
import pathlib
import re
from dataclasses import dataclass, field, asdict
from typing import List


def slugify(text: str) -> str:
    text = re.sub(r"[\\/:*?\"<>|\s]+", "-", text.strip())
    return text[:50].strip("-") or "video"


@dataclass
class Scene:
    """1 シーン（1 画面）分。"""

    onscreen: str    # 画面に出す短いテロップ
    narration: str   # 読み上げる文章（話し言葉）


@dataclass
class VideoScript:
    """ショート動画 1 本の台本。"""

    hook: str                 # 冒頭2秒で掴む強い一言
    scenes: List[Scene]
    caption: str              # 投稿時のキャプション
    hashtags: List[str] = field(default_factory=list)

    def all_scenes(self) -> List[Scene]:
        """フックを先頭シーンに加えた、描画用の全シーン列。"""
        return [Scene(onscreen=self.hook, narration=self.hook), *self.scenes]

    def caption_text(self) -> str:
        tags = " ".join(f"#{t}" for t in self.hashtags)
        return f"{self.caption}\n\n{tags}".strip() + "\n"

    def to_dict(self) -> dict:
        return {
            "hook": self.hook,
            "scenes": [asdict(s) for s in self.scenes],
            "caption": self.caption,
            "hashtags": self.hashtags,
        }

    def save_sidecar(self, directory: str | pathlib.Path, stem: str) -> pathlib.Path:
        """キャプション(.txt)と台本(.json)を保存し、txt のパスを返す。"""
        directory = pathlib.Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"{stem}.json").write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        txt = directory / f"{stem}.txt"
        txt.write_text(self.caption_text(), encoding="utf-8")
        return txt

    @staticmethod
    def default_stem(hook: str) -> str:
        return f"{_dt.date.today().isoformat()}-{slugify(hook)}"
