"""オーケストレーション: 台本 → 音声 → 画像 → 動画 を一気通貫で行う."""

from __future__ import annotations

import logging
import pathlib
import tempfile
from typing import Optional

import anthropic

from .config import TikTokConfig
from . import render, voice
from .models import VideoScript
from .script import generate_script

logger = logging.getLogger("tiktok_auto")


def make_video(
    cfg: TikTokConfig,
    client: Optional[anthropic.Anthropic] = None,
    script: Optional[VideoScript] = None,
) -> pathlib.Path:
    """ショート動画を 1 本生成し、できあがった MP4 のパスを返す.

    キャプション/ハッシュタグ(.txt) と台本(.json) も同じ場所に保存する。
    """
    client = client or anthropic.Anthropic()
    out_dir = pathlib.Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if script is None:
        logger.info("台本を生成中（テーマ: %s）...", cfg.theme)
        script = generate_script(cfg, client=client)

    stem = VideoScript.default_stem(script.hook)
    mp4_path = out_dir / f"{stem}.mp4"

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        clips = []
        for i, scene in enumerate(script.all_scenes()):
            logger.info("シーン %d を作成中: %s", i + 1, scene.onscreen)
            audio = voice.synthesize(scene.narration, tmp / f"a{i}.mp3", cfg)
            frame = render.make_frame(scene.onscreen, tmp / f"f{i}.png", cfg)
            clip = render.scene_clip(frame, audio, tmp / f"s{i}.mp4")
            clips.append(clip)
        render.concat(clips, mp4_path, tmp)

    sidecar = script.save_sidecar(out_dir, stem)
    logger.info("完成: %s（キャプション: %s）", mp4_path, sidecar)
    return mp4_path
