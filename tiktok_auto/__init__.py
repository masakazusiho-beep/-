"""tiktok_auto — 顔出しなしショート動画の自動生成パイプライン.

台本生成(Claude) → ナレーション(無料TTS: edge-tts) → テロップ画像(Pillow) →
動画組み立て(ffmpeg) で、TikTok 向けの縦型 MP4 を自動生成する。

投稿は手動（できあがった MP4 をアップロード）。生成だけを自動化する。
"""

from .config import TikTokConfig
from .models import Scene, VideoScript

__all__ = ["TikTokConfig", "Scene", "VideoScript"]

__version__ = "0.1.0"
