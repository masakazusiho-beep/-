"""フルパイプライン: 生成 → 保存 →（任意で）Threads へ投稿."""

from __future__ import annotations

import logging
import pathlib
from dataclasses import dataclass, field
from typing import List, Optional

import anthropic

from .config import ThreadsAutoConfig
from .generate import generate_posts
from .models import Post

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    posts: List[Post] = field(default_factory=list)
    saved: List[str] = field(default_factory=list)
    published: List[str] = field(default_factory=list)


def collect_past_posts(*dirs: str, limit: int = 20) -> List[str]:
    """過去の投稿ドラフト(.md)の冒頭を集める（重複回避用）."""
    texts: List[str] = []
    for d in dirs:
        p = pathlib.Path(d)
        if not p.exists():
            continue
        for md in sorted(p.glob("*.md"), reverse=True):
            try:
                first = md.read_text(encoding="utf-8").strip().splitlines()[0]
            except (OSError, IndexError):
                continue
            texts.append(first.strip())
            if len(texts) >= limit:
                return texts
    return texts


def run_pipeline(
    cfg: ThreadsAutoConfig,
    count: int = 3,
    dry_run: bool = True,
    client: Optional[anthropic.Anthropic] = None,
    history_dirs: Optional[List[str]] = None,
) -> PipelineResult:
    """投稿を生成して保存する。dry_run=False かつ cfg.publish=True なら Threads へ投稿."""
    client = client or anthropic.Anthropic()
    result = PipelineResult()

    dirs = history_dirs if history_dirs is not None else ["threads", cfg.output_dir]
    avoid = collect_past_posts(*dirs)
    logger.info("Threads 投稿を %d 件生成中（既出 %d 件を回避）...", count, len(avoid))
    result.posts = generate_posts(cfg, count=count, client=client, avoid=avoid)

    for i, post in enumerate(result.posts):
        result.saved.append(str(post.save(cfg.output_dir, index=i)))
    logger.info("%d 件を %s に保存しました", len(result.saved), cfg.output_dir)

    if not dry_run and cfg.publish:
        cfg.require_credentials()
        from .poster import post_text
        for post in result.posts:
            r = post_text(cfg.threads_user_id, cfg.threads_token, post.text)
            result.published.append(("OK " if r.ok else "NG ") + r.detail)
            logger.info("投稿: %s", result.published[-1])

    return result
