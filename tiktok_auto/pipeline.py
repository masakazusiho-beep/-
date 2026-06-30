"""オーケストレーション: 台本 → 音声 → 画像 → 動画 を一気通貫で行う."""

from __future__ import annotations

import logging
import pathlib
import tempfile
from typing import Optional

import anthropic

from .config import TikTokConfig
from . import render, voice
from .models import DialogueScript, VideoScript
from .script import generate_dialogue, generate_script

logger = logging.getLogger("tiktok_auto")


def make_video(
    cfg: TikTokConfig,
    client: Optional[anthropic.Anthropic] = None,
    script: Optional[VideoScript] = None,
) -> pathlib.Path:
    """設定の style に応じてショート動画を 1 本生成する."""
    if cfg.style == "dialogue" and script is None:
        return make_dialogue_video(cfg, client=client)
    return _make_plain_video(cfg, client=client, script=script)


def _make_plain_video(
    cfg: TikTokConfig,
    client: Optional[anthropic.Anthropic] = None,
    script: Optional[VideoScript] = None,
) -> pathlib.Path:
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


def make_dialogue_video(
    cfg: TikTokConfig,
    client: Optional[anthropic.Anthropic] = None,
    script: Optional[DialogueScript] = None,
) -> pathlib.Path:
    """会話形式（材料キャラの掛け合い）のショート動画を 1 本生成する."""
    client = client or anthropic.Anthropic()
    out_dir = pathlib.Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if script is None:
        logger.info("会話台本を生成中（テーマ: %s）...", cfg.theme)
        script = generate_dialogue(cfg, client=client)

    stem = VideoScript.default_stem(script.title)
    mp4_path = out_dir / f"{stem}.mp4"

    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        clips = []
        for i, turn in enumerate(script.turns):
            speaker_voice = cfg.voice if turn.speaker == 0 else cfg.voice_b
            logger.info("ターン %d（%s）...", i + 1, script.characters[turn.speaker].name)
            audio = voice.synthesize(turn.line, tmp / f"a{i}.mp3", cfg, voice=speaker_voice)
            frame = render.make_dialogue_frame(turn, script, tmp / f"f{i}.png", cfg)
            clip = render.scene_clip(frame, audio, tmp / f"s{i}.mp4")
            clips.append(clip)
        render.concat(clips, mp4_path, tmp)

    sidecar = script.save_sidecar(out_dir, stem)
    logger.info("完成: %s（キャプション: %s）", mp4_path, sidecar)
    return mp4_path
