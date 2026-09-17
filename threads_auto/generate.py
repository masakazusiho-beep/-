"""投稿生成: Claude に Threads 向けの短文投稿を書かせる."""

from __future__ import annotations

import json
import re
from typing import List, Optional

import anthropic

from .config import ThreadsAutoConfig
from .models import Post

# 投稿の切り口を毎回散らすためのカテゴリ
_CATEGORIES = [
    "お菓子作りのちょっとしたコツ",
    "あるあるな失敗談・共感ネタ",
    "読者に問いかける質問（2択など）",
    "使ってよかった道具・材料の紹介",
    "作っている最中の裏側・情景",
    "初心者へのやさしいアドバイス",
]


def _build_prompt(cfg: ThreadsAutoConfig, count: int, avoid: Optional[List[str]] = None) -> str:
    kw = "、".join(cfg.keywords) if cfg.keywords else "（指定なし）"
    cats = "、".join(_CATEGORIES)
    where = cfg.page_url if cfg.page_url else "プロフィールのリンク"
    lines = [
        "あなたは Threads（スレッズ）で人気の、お菓子作り系クリエイターです。",
        f"テーマ「{cfg.theme or 'お菓子作り'}」で、そのまま投稿できる短い投稿文を {count} 個作ってください。",
        f"重視キーワード: {kw}",
        "",
        "【守ること】",
        f"- 1投稿は {cfg.max_chars} 文字以内。短く、リズムよく。",
        "- 1行目で興味を引く。絵文字は使いすぎない（0〜3個程度）。",
        f"- 毎回ちがう切り口にする（例: {cats}）。似た投稿を並べない。",
        "- ハッシュタグの羅列はしない。宣伝くさくしない。",
        f"- {count} 個のうち一部（半分以下）にだけ、さりげなく「{where}」へ誘導する一言を入れる。",
        "- 生のアフィリエイトリンクは書かない（誘導は上記の場所のみ）。",
    ]
    if avoid:
        recent = "\n".join(f"- {t}" for t in avoid[:20])
        lines += ["", "【最近の投稿（内容がかぶらないように）】", recent]
    lines += [
        "",
        '出力は次の JSON オブジェクトのみ:',
        '{"posts": ["投稿文1", "投稿文2", ...]}',
    ]
    return "\n".join(lines)


def _extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("Claude の応答から JSON を取得できませんでした")
    return json.loads(match.group(0))


def generate_posts(
    cfg: ThreadsAutoConfig,
    count: int = 3,
    client: Optional[anthropic.Anthropic] = None,
    avoid: Optional[List[str]] = None,
) -> List[Post]:
    """Threads 投稿を `count` 個生成して返す."""
    client = client or anthropic.Anthropic()
    prompt = _build_prompt(cfg, count, avoid=avoid)

    resp = client.messages.create(
        model=cfg.model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    data = _extract_json(text)

    posts: List[Post] = []
    for item in data.get("posts", []):
        body = item.strip() if isinstance(item, str) else str(item.get("text", "")).strip()
        if not body:
            continue
        if len(body) > cfg.max_chars:
            body = body[: cfg.max_chars].rstrip()
        posts.append(Post(text=body))
    return posts
