"""台本生成: Claude に TikTok 向けショート動画の台本を書かせる."""

from __future__ import annotations

import json

import anthropic

from .config import TikTokConfig
from .models import Scene, VideoScript

_SCHEMA = {
    "type": "object",
    "properties": {
        "hook": {"type": "string"},
        "scenes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "onscreen": {"type": "string"},
                    "narration": {"type": "string"},
                },
                "required": ["onscreen", "narration"],
                "additionalProperties": False,
            },
        },
        "caption": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["hook", "scenes", "caption", "hashtags"],
    "additionalProperties": False,
}


def _prompt(cfg: TikTokConfig) -> str:
    kw = "、".join(cfg.keywords) if cfg.keywords else "（指定なし）"
    n = max(3, min(6, cfg.target_seconds // 6))  # 1シーン約6秒の目安
    return "\n".join(
        [
            "あなたはバズるTikTokショート動画の構成作家です。",
            f"テーマ「{cfg.theme or '指定なし'}」で、約{cfg.target_seconds}秒の縦型ショート動画の台本を作ってください。",
            f"重視キーワード: {kw}",
            "",
            "次のルールで作ってください:",
            "- hook: 最初の2秒で指を止めさせる強い一言（短く、煽りすぎず具体的に）",
            f"- scenes: {n}個前後。各シーンに onscreen と narration を入れる",
            "  - onscreen: 画面に大きく出すテロップ。15文字以内のごく短い言葉",
            "  - narration: 読み上げる話し言葉。1〜2文の自然な口語",
            "- 視聴者が最後まで見たくなるよう、結論を最後に置いて引っぱる",
            "- caption: 投稿文（一言＋共感や問いかけ）",
            "- hashtags: 関連タグを5個前後（#は付けず単語のみ）",
            "",
            "AIっぽい紋切り型は避け、テンポよく、親しみやすく。",
        ]
    )


def generate_script(cfg: TikTokConfig, client: anthropic.Anthropic | None = None) -> VideoScript:
    """台本を 1 本生成する."""
    client = client or anthropic.Anthropic()
    resp = client.messages.create(
        model=cfg.model,
        max_tokens=4000,
        thinking={"type": "adaptive"},
        output_config={
            "effort": cfg.effort,
            "format": {"type": "json_schema", "schema": _SCHEMA},
        },
        messages=[{"role": "user", "content": _prompt(cfg)}],
    )
    text = next(b.text for b in resp.content if b.type == "text")
    return parse_script(text)


def parse_script(text: str) -> VideoScript:
    """Claude の JSON 応答を VideoScript に変換する."""
    data = json.loads(text)
    return VideoScript(
        hook=data["hook"],
        scenes=[Scene(onscreen=s["onscreen"], narration=s["narration"]) for s in data["scenes"]],
        caption=data.get("caption", ""),
        hashtags=list(data.get("hashtags", [])),
    )
