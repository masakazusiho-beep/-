"""コマンドラインインターフェース.

    python -m tiktok_auto script --config note_config.toml          # 台本だけ確認
    python -m tiktok_auto make   --config note_config.toml          # 動画を1本作る
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import List

from .config import TikTokConfig
from .pipeline import make_video
from .script import generate_script


def _load_cfg(args) -> TikTokConfig:
    cfg = TikTokConfig.load(getattr(args, "config", None))
    if getattr(args, "theme", None):
        cfg.theme = args.theme
    return cfg


def _cmd_script(args) -> int:
    cfg = _load_cfg(args)
    s = generate_script(cfg)
    print(f"\n【フック】{s.hook}\n")
    for i, sc in enumerate(s.scenes, 1):
        print(f"[{i}] テロップ: {sc.onscreen}")
        print(f"    ナレーション: {sc.narration}")
    print(f"\n【キャプション】\n{s.caption_text()}")
    return 0


def _cmd_make(args) -> int:
    cfg = _load_cfg(args)
    path = make_video(cfg)
    print(f"動画を作成しました: {path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tiktok_auto", description="ショート動画の自動生成")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, func, help_text in (
        ("script", _cmd_script, "台本だけ生成して表示"),
        ("make", _cmd_make, "動画を1本作る"),
    ):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--config", help="TOML 設定ファイル（note_config.toml を共有可）")
        p.add_argument("--theme", help="テーマ（設定を上書き）")
        p.add_argument("--verbose", action="store_true")
        p.set_defaults(func=func)

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
