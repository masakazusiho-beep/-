"""ナレーション生成: edge-tts（無料・APIキー不要）で読み上げ音声を作る."""

from __future__ import annotations

import asyncio
import pathlib
import subprocess

from .config import TikTokConfig


def synthesize(text: str, out_path: str | pathlib.Path, cfg: TikTokConfig,
               voice: str | None = None) -> pathlib.Path:
    """text を読み上げた MP3 を out_path に書き出す（voice で声を上書き可）."""
    try:
        import edge_tts
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("edge-tts が必要です: pip install edge-tts") from exc

    out_path = pathlib.Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    async def _run() -> None:
        communicate = edge_tts.Communicate(text, voice or cfg.voice, rate=cfg.speech_rate)
        await communicate.save(str(out_path))

    asyncio.run(_run())
    return out_path


def audio_duration(path: str | pathlib.Path) -> float:
    """ffprobe で音声の長さ（秒）を返す."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())
