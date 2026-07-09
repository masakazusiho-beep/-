"""ネタ収集・分析: Claude にトレンドを踏まえた記事ネタを提案させる.

`research=True` のときは web 検索ツールを有効にし、最新トレンドを踏まえて提案する。
"""

from __future__ import annotations

import json
import re
from typing import List

import anthropic

from .config import NoteAutoConfig
from .models import Idea
from .playbook import idea_guidance

# web 検索の最新バリアント（Opus 4.8 対応）。動的フィルタリング内蔵。
_WEB_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search"}

_IDEA_SCHEMA = {
    "type": "object",
    "properties": {
        "ideas": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "angle": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "rationale": {"type": "string"},
                },
                "required": ["title", "angle", "keywords", "rationale"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["ideas"],
    "additionalProperties": False,
}


def _build_prompt(cfg: NoteAutoConfig, count: int, research: bool) -> str:
    kw = "、".join(cfg.keywords) if cfg.keywords else "（指定なし）"
    lines = [
        f"あなたは note の人気クリエイターの編集パートナーです。",
        f"テーマ「{cfg.theme or '指定なし'}」に沿って、読者の役に立つ記事ネタを {count} 個提案してください。",
        f"重視キーワード: {kw}",
        "",
        "各ネタには次を含めてください:",
        "- title: 思わずクリックしたくなる具体的な日本語タイトル",
        "- angle: 記事の切り口・読者が得る価値",
        "- keywords: SEO/検索を意識したキーワード 3〜5 個",
        "- rationale: なぜ今このネタが刺さるのか（根拠・トレンド）",
        "",
        idea_guidance(),
    ]
    if cfg.extra_guidance:
        lines += ["", "【追加の方針】", cfg.extra_guidance]
    if research:
        lines += [
            "",
            "web 検索を使って最新のトレンドや競合記事を調べ、被りを避けつつ"
            "今まさに需要のある切り口を選んでください。",
        ]
    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    """テキストから最初の JSON オブジェクトを抜き出してパースする."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("Claude の応答から JSON を取得できませんでした")
    return json.loads(match.group(0))


def generate_ideas(
    cfg: NoteAutoConfig,
    count: int = 5,
    research: bool = False,
    client: anthropic.Anthropic | None = None,
) -> List[Idea]:
    """記事ネタを `count` 個生成して返す."""
    client = client or anthropic.Anthropic()
    prompt = _build_prompt(cfg, count, research)

    if research:
        # web 検索ツールと併用するため、構造化出力ではなく JSON 指示＋抽出で対応。
        prompt += "\n\n出力は {\"ideas\": [...]} という JSON オブジェクトのみにしてください。"
        resp = client.messages.create(
            model=cfg.model,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            output_config={"effort": cfg.effort},
            tools=[_WEB_SEARCH_TOOL],
            messages=[{"role": "user", "content": prompt}],
        )
        text = "".join(b.text for b in resp.content if b.type == "text")
        data = _extract_json(text)
    else:
        # 構造化出力でスキーマを保証。
        resp = client.messages.create(
            model=cfg.model,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            output_config={
                "effort": cfg.effort,
                "format": {"type": "json_schema", "schema": _IDEA_SCHEMA},
            },
            messages=[{"role": "user", "content": prompt}],
        )
        text = next(b.text for b in resp.content if b.type == "text")
        data = json.loads(text)

    return [
        Idea(
            title=item["title"],
            angle=item.get("angle", ""),
            keywords=list(item.get("keywords", [])),
            rationale=item.get("rationale", ""),
        )
        for item in data.get("ideas", [])
    ]
