"""オーケストレーション: ネタ収集 → 生成 → 投稿 を順に実行する."""

from __future__ import annotations

import logging
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


def run_pipeline(
    cfg: NoteAutoConfig,
    count: int = 1,
    research: bool = False,
    dry_run: bool = True,
    client: Optional[anthropic.Anthropic] = None,
) -> PipelineResult:
    """フルパイプラインを実行する.

    Args:
        count: 生成する記事の本数。
        research: web 検索でトレンドを踏まえてネタ出しするか。
        dry_run: True ならローカル保存のみ（note へは投稿しない）。
            False のときは `cfg.publish` に従い、下書き保存または公開する。
    """
    client = client or anthropic.Anthropic()
    result = PipelineResult()

    logger.info("ネタを %d 件生成中（research=%s）...", count, research)
    result.ideas = generate_ideas(cfg, count=count, research=research, client=client)

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
