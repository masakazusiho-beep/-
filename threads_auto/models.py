"""threads_auto のデータ構造."""

from __future__ import annotations

import datetime as _dt
import pathlib
from dataclasses import dataclass, field


@dataclass
class Post:
    """生成済みの Threads 投稿（1本）."""

    text: str
    created_at: str = field(default_factory=lambda: _dt.datetime.now().isoformat(timespec="seconds"))

    def save(self, directory: str | pathlib.Path, index: int = 0) -> pathlib.Path:
        """投稿を Markdown として保存し、そのパスを返す."""
        directory = pathlib.Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        stamp = _dt.datetime.now().strftime("%Y-%m-%d-%H%M%S")
        path = directory / f"{stamp}-{index}.md"
        path.write_text(self.text.strip() + "\n", encoding="utf-8")
        return path
