"""パイプラインで受け渡すデータ構造."""

from __future__ import annotations

import datetime as _dt
import json
import pathlib
import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional


def _slugify(text: str) -> str:
    """ファイル名向けに安全な slug を作る（日本語は残しつつ記号を除去）."""
    text = text.strip()
    text = re.sub(r"[\\/:*?\"<>|\s]+", "-", text)
    return text[:60].strip("-") or "untitled"


@dataclass
class Idea:
    """記事のネタ（1本分）."""

    title: str
    angle: str = ""          # 切り口・狙い
    keywords: List[str] = field(default_factory=list)
    rationale: str = ""      # なぜ今このネタか（トレンド分析の結果など）

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Article:
    """生成済みの記事."""

    title: str
    body: str                # 本文（Markdown）
    tags: List[str] = field(default_factory=list)
    idea: Optional[Idea] = None
    created_at: str = field(default_factory=lambda: _dt.datetime.now().isoformat(timespec="seconds"))

    def to_dict(self) -> dict:
        d = asdict(self)
        return d

    def save(self, directory: str | pathlib.Path) -> pathlib.Path:
        """記事を Markdown + JSON サイドカーとして保存し、Markdown のパスを返す."""
        directory = pathlib.Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        stem = f"{_dt.date.today().isoformat()}-{_slugify(self.title)}"
        md_path = directory / f"{stem}.md"
        md_path.write_text(self._as_markdown(), encoding="utf-8")
        (directory / f"{stem}.json").write_text(
            json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return md_path

    def _as_markdown(self) -> str:
        tag_line = " ".join(f"#{t}" for t in self.tags)
        parts = [f"# {self.title}", "", self.body.strip()]
        if tag_line:
            parts += ["", "---", tag_line]
        return "\n".join(parts) + "\n"
