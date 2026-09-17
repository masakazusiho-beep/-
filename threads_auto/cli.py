"""コマンドラインインターフェース（threads_auto）.

使い方:
    python -m threads_auto run --config threads_config.toml --count 3          # 生成のみ
    python -m threads_auto run --config threads_config.toml --count 3 --post   # Threads へ投稿
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List

from .config import ThreadsAutoConfig
from .pipeline import run_pipeline


def _load_cfg(args) -> ThreadsAutoConfig:
    cfg = ThreadsAutoConfig.load(getattr(args, "config", None))
    if getattr(args, "theme", None):
        cfg.theme = args.theme
    return cfg


def _cmd_run(args) -> int:
    cfg = _load_cfg(args)
    if args.post:
        cfg.publish = True
    result = run_pipeline(cfg, count=args.count, dry_run=not args.post)
    print(f"\n生成: {len(result.posts)} 投稿")
    for i, post in enumerate(result.posts, 1):
        preview = post.text.replace("\n", " ")
        if len(preview) > 40:
            preview = preview[:40] + "…"
        print(f"  [{i}] {preview}  ({len(post.text)} 文字)")
    for pub in result.published:
        print(f"  [投稿] {pub}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="threads_auto", description="Threads 投稿の自動生成")
    sub = parser.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="投稿を生成→（任意で）Threads へ投稿")
    p_run.add_argument("--config", help="TOML 設定ファイルのパス")
    p_run.add_argument("--theme", help="テーマ（設定ファイルを上書き）")
    p_run.add_argument("--count", type=int, default=3)
    p_run.add_argument("--post", action="store_true", help="Threads へ投稿する（既定は生成のみ）")
    p_run.add_argument("--verbose", action="store_true", help="詳細ログを出力")
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
