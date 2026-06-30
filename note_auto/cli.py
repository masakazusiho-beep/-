"""コマンドラインインターフェース.

使い方:
    python -m note_auto ideas   --config note_config.toml --count 5 --research
    python -m note_auto generate --config note_config.toml --title "..."
    python -m note_auto run     --config note_config.toml --count 1        # ドライラン
    python -m note_auto run     --config note_config.toml --count 1 --post # note へ投稿
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List

from .config import NoteAutoConfig
from .generate import generate_article
from .ideas import generate_ideas
from .models import Idea
from .pipeline import run_pipeline


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", help="TOML 設定ファイルのパス")
    parser.add_argument("--theme", help="テーマ（設定ファイルを上書き）")
    parser.add_argument("--verbose", action="store_true", help="詳細ログを出力")


def _load_cfg(args) -> NoteAutoConfig:
    cfg = NoteAutoConfig.load(getattr(args, "config", None))
    if getattr(args, "theme", None):
        cfg.theme = args.theme
    return cfg


def _cmd_ideas(args) -> int:
    cfg = _load_cfg(args)
    ideas = generate_ideas(cfg, count=args.count, research=args.research)
    for i, idea in enumerate(ideas, 1):
        print(f"\n[{i}] {idea.title}")
        print(f"    切り口: {idea.angle}")
        print(f"    キーワード: {', '.join(idea.keywords)}")
        print(f"    狙い: {idea.rationale}")
    return 0


def _cmd_generate(args) -> int:
    cfg = _load_cfg(args)
    idea = Idea(title=args.title, angle=args.angle or "", keywords=args.keywords or [])
    article = generate_article(cfg, idea)
    path = article.save(cfg.output_dir)
    print(f"記事を保存しました: {path}")
    return 0


def _cmd_run(args) -> int:
    cfg = _load_cfg(args)
    if args.post:
        cfg.publish = args.publish  # --publish 指定時は公開、無指定なら下書き保存
    result = run_pipeline(
        cfg,
        count=args.count,
        research=args.research,
        dry_run=not args.post,
    )
    print(f"\n生成: {len(result.articles)} 記事")
    for art in result.articles:
        print(f"  - {art.title}  ({len(art.body)} 文字, tags={art.tags})")
    for pub in result.published:
        status = "OK" if pub.ok else "NG"
        print(f"  [投稿:{status}] {pub.detail}  {pub.url or ''}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="note_auto", description="note 記事の自動化パイプライン")
    sub = parser.add_subparsers(dest="command", required=True)

    p_ideas = sub.add_parser("ideas", help="記事ネタを生成する")
    _add_common(p_ideas)
    p_ideas.add_argument("--count", type=int, default=5)
    p_ideas.add_argument("--research", action="store_true", help="web 検索でトレンドを調べる")
    p_ideas.set_defaults(func=_cmd_ideas)

    p_gen = sub.add_parser("generate", help="指定タイトルで記事を1本生成する")
    _add_common(p_gen)
    p_gen.add_argument("--title", required=True)
    p_gen.add_argument("--angle")
    p_gen.add_argument("--keywords", nargs="*")
    p_gen.set_defaults(func=_cmd_generate)

    p_run = sub.add_parser("run", help="ネタ出し→生成→（任意で）投稿まで実行")
    _add_common(p_run)
    p_run.add_argument("--count", type=int, default=1)
    p_run.add_argument("--research", action="store_true")
    p_run.add_argument("--post", action="store_true", help="note へ投稿する（既定はドライラン）")
    p_run.add_argument("--publish", action="store_true", help="--post 時に下書きではなく公開する")
    p_run.set_defaults(func=_cmd_run)

    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if getattr(args, "verbose", False) else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
