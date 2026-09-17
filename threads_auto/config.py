"""設定の読み込み（threads_auto）.

機密情報（API キー・Threads のトークン）は環境変数から読む。リポジトリには
コミットしないこと。
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

# 投稿文は短いので、コストの安い軽量モデルを既定にする。
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


@dataclass
class ThreadsAutoConfig:
    """Threads 投稿自動生成の設定."""

    # --- コンテンツ方針 ---
    theme: str = ""
    keywords: List[str] = field(default_factory=list)
    tone: str = "親しみやすく、共感を呼ぶカジュアルな語り口"
    max_chars: int = 500                              # Threads の投稿上限
    cta_ratio: float = 0.4                            # 何割の投稿に誘導文を入れるか（0〜1）
    page_url: str = ""                                # 誘導先（おすすめページ等）。空なら「プロフィール」と表現

    # --- 生成 ---
    model: str = DEFAULT_MODEL

    # --- 出力 ---
    output_dir: str = "threads-drafts"

    # --- Threads へ自動投稿（任意）---
    threads_user_id: Optional[str] = None             # 環境変数 THREADS_USER_ID
    threads_token: Optional[str] = None               # 環境変数 THREADS_TOKEN
    publish: bool = False                             # True で Threads へ実際に投稿

    @classmethod
    def load(cls, path: Optional[str | pathlib.Path] = None) -> "ThreadsAutoConfig":
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
        threads = data.get("threads", {})

        cfg = cls(
            theme=content.get("theme", ""),
            keywords=list(content.get("keywords", [])),
            tone=content.get("tone", cls.tone),
            max_chars=int(content.get("max_chars", cls.max_chars)),
            cta_ratio=float(content.get("cta_ratio", cls.cta_ratio)),
            page_url=content.get("page_url", ""),
            model=gen.get("model", DEFAULT_MODEL),
            output_dir=out.get("output_dir", cls.output_dir),
            publish=bool(threads.get("publish", False)),
        )

        # 機密情報は環境変数から
        cfg.threads_user_id = os.environ.get("THREADS_USER_ID", cfg.threads_user_id)
        cfg.threads_token = os.environ.get("THREADS_TOKEN", cfg.threads_token)
        if os.environ.get("THREADS_AUTO_PUBLISH"):
            cfg.publish = os.environ["THREADS_AUTO_PUBLISH"].lower() in ("1", "true", "yes")

        return cfg

    def require_credentials(self) -> None:
        missing = [
            name
            for name, val in (("THREADS_USER_ID", self.threads_user_id), ("THREADS_TOKEN", self.threads_token))
            if not val
        ]
        if missing:
            raise RuntimeError(
                "Threads の認証情報が未設定です。環境変数を設定してください: " + ", ".join(missing)
            )
