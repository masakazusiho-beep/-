"""設定の読み込み.

機密情報（API キー・note のログイン情報）は環境変数から読む。リポジトリには
コミットしないこと。`examples/note_config.example.toml` も参照。
"""

from __future__ import annotations

import os
import pathlib
from dataclasses import dataclass, field
from typing import List, Optional

try:  # tomllib は Python 3.11+ 標準
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None  # type: ignore

# 記事生成に使う Claude モデル。最新かつ高性能な Opus 4.8 を既定にする。
DEFAULT_MODEL = "claude-opus-4-8"


@dataclass
class NoteAutoConfig:
    """パイプライン全体の設定."""

    # --- コンテンツ方針 ---
    theme: str = ""                                   # 全体テーマ
    keywords: List[str] = field(default_factory=list)
    tone: str = "親しみやすく、具体例を交えた丁寧な語り口"
    target_chars: int = 2000                          # 目安文字数
    default_tags: List[str] = field(default_factory=list)

    # --- 生成 ---
    model: str = DEFAULT_MODEL
    effort: str = "high"                              # low|medium|high|max
    paid: bool = False                                # True で「有料記事」形式（無料部分→🔒→濃い本編）

    # --- 出力 ---
    output_dir: str = "drafts"

    # --- note 投稿（Playwright） ---
    note_email: Optional[str] = None                  # 環境変数 NOTE_EMAIL
    note_password: Optional[str] = None               # 環境変数 NOTE_PASSWORD
    publish: bool = False                             # True で公開、False は下書き保存まで
    headless: bool = True

    @classmethod
    def load(cls, path: Optional[str | pathlib.Path] = None) -> "NoteAutoConfig":
        """TOML ファイル（任意）＋環境変数から設定を組み立てる.

        環境変数が常に TOML より優先される（機密情報は環境変数に置くため）。
        """
        data: dict = {}
        if path:
            p = pathlib.Path(path)
            if p.exists():
                if tomllib is None:  # pragma: no cover
                    raise RuntimeError("TOML 設定には Python 3.11+ が必要です")
                data = tomllib.loads(p.read_text(encoding="utf-8"))

        content = data.get("content", {})
        gen = data.get("generation", {})
        out = data.get("output", {})
        note = data.get("note", {})

        cfg = cls(
            theme=content.get("theme", ""),
            keywords=list(content.get("keywords", [])),
            tone=content.get("tone", cls.tone),
            target_chars=int(content.get("target_chars", cls.target_chars)),
            default_tags=list(content.get("default_tags", [])),
            model=gen.get("model", DEFAULT_MODEL),
            effort=gen.get("effort", cls.effort),
            paid=bool(gen.get("paid", False)),
            output_dir=out.get("output_dir", cls.output_dir),
            publish=bool(note.get("publish", False)),
            headless=bool(note.get("headless", True)),
        )

        # 機密情報は環境変数を優先（TOML に書かせない）
        cfg.note_email = os.environ.get("NOTE_EMAIL", cfg.note_email)
        cfg.note_password = os.environ.get("NOTE_PASSWORD", cfg.note_password)

        # CI などで上書きしたい一般設定も環境変数で受ける
        if os.environ.get("NOTE_AUTO_PUBLISH"):
            cfg.publish = os.environ["NOTE_AUTO_PUBLISH"].lower() in ("1", "true", "yes")

        return cfg

    def require_credentials(self) -> None:
        """note 投稿に必要な認証情報が揃っているか検証する."""
        missing = [
            name
            for name, val in (("NOTE_EMAIL", self.note_email), ("NOTE_PASSWORD", self.note_password))
            if not val
        ]
        if missing:
            raise RuntimeError(
                "note のログイン情報が未設定です。環境変数を設定してください: " + ", ".join(missing)
            )
