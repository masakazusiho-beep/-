"""オーケストレーション: ネタ収集 → 生成 → 投稿 を順に実行する."""

from __future__ import annotations

import logging
import pathlib
from dataclasses import dataclass, field
from typing import List, Optional

import anthropic

from .config import NoteAutoConfig
from .generate import generate_article
from .ideas import generate_ideas
from .models import Article, Idea
from .publish import PublishResult, publish_to_note, save_locally

logger = logging.getLogger("note_auto")


@dataclass
class PipelineResult:
    ideas: List[Idea] = field(default_factory=list)
    articles: List[Article] = field(default_factory=list)
    published: List[PublishResult] = field(default_factory=list)


def collect_past_titles(*dirs: str) -> List[str]:
    """過去記事(.md)の見出しからタイトル一覧を集める（重複ネタ回避用）."""
    titles: List[str] = []
    for d in dirs:
        p = pathlib.Path(d)
        if not p.exists():
            continue
        for md in sorted(p.glob("*.md")):
            try:
                first = md.read_text(encoding="utf-8").lstrip().splitlines()[0]
            except (OSError, IndexError):
                continue
            titles.append(first.lstrip("# ").strip())
    return titles


def run_pipeline(
    cfg: NoteAutoConfig,
    count: int = 1,
    research: bool = False,
    dry_run: bool = True,
    client: Optional[anthropic.Anthropic] = None,
    history_dirs: Optional[List[str]] = None,
) -> PipelineResult:
    """フルパイプラインを実行する.

    Args:
        count: 生成する記事の本数。
        research: web 検索でトレンドを踏まえてネタ出しするか。
        dry_run: True ならローカル保存のみ（note へは投稿しない）。
            False のときは `cfg.publish` に従い、下書き保存または公開する。
        history_dirs: 過去記事があるフォルダ（既定: articles と出力先）。
            ここのタイトルと被らないネタを出す。
    """
    client = client or anthropic.Anthropic()
    result = PipelineResult()

    dirs = history_dirs if history_dirs is not None else ["articles", cfg.output_dir]
    avoid = collect_past_titles(*dirs)
    logger.info("ネタを %d 件生成中（research=%s, 既出 %d 件を回避）...", count, research, len(avoid))
    result.ideas = generate_ideas(
        cfg, count=count, research=research, client=client, avoid_titles=avoid
    )

    for idea in result.ideas:
        logger.info("記事を生成中: %s", idea.title)
        article = generate_article(cfg, idea, client=client)
        result.articles.append(article)

        # 常にローカルにも保存しておく（証跡・人手レビュー用）
        path = save_locally(cfg, article)
        logger.info("下書きを保存: %s", path)

        if not dry_run:
            logger.info("note に投稿中（publish=%s）...", cfg.publish)
            result.published.append(publish_to_note(cfg, article))

    return result
