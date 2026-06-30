"""記事生成: ネタ（Idea）から note 向けの本文を Claude に書かせる.

長文になりうるのでストリーミングで生成し、`get_final_message()` で確定させる
（リクエストタイムアウト回避）。
"""

from __future__ import annotations

import json
import re
from typing import Optional

import anthropic

from .config import NoteAutoConfig
from .models import Article, Idea

# タイトルとタグを末尾の JSON フェンスで受け取り、本文と分離する。
_META_RE = re.compile(r"```json\s*(\{.*?\})\s*```\s*$", re.DOTALL)


def _system_prompt(cfg: NoteAutoConfig) -> str:
    return (
        "あなたはプロの note ライターです。読者の心に残り、最後まで読まれる記事を書きます。"
        f"文体は「{cfg.tone}」。"
        "Markdown で、適切な見出し(##)・箇条書き・強調を使って読みやすく構成してください。"
        "導入で関心を引き、本文で具体的な価値を届け、結びで行動や余韻を残します。"
        "AI が書いたとわかる紋切り型の言い回しや過度な定型句は避けてください。"
    )


def _user_prompt(cfg: NoteAutoConfig, idea: Idea) -> str:
    kw = "、".join(idea.keywords) if idea.keywords else "（指定なし）"
    lines = [
        f"次のネタで note 記事を書いてください。",
        f"- タイトル案: {idea.title}",
        f"- 切り口: {idea.angle or '指定なし'}",
        f"- キーワード: {kw}",
        f"- 目安の文字数: {cfg.target_chars} 字前後",
    ]
    if cfg.paid:
        lines += [
            "",
            "【有料記事の構成にすること】",
            "- 冒頭の無料部分で読者を引き込み、『結論』までは見せる。",
            "- そのあと「🔒 ここから先は有料記事です」という見出しで区切る。",
            "- 有料部分は、具体的な数字・選び方・手順など『お金を払う価値』のある濃い内容にする。",
            "- 後半に『予算別の表』か『チェックリスト』を必ず1つ入れる。",
        ]
    lines += [
        "",
        "本文は Markdown 本文のみ（記事タイトルの見出しは付けない）。",
        "本文の最後に、メタ情報を次の形式の JSON コードブロックで1つだけ付けてください:",
        '```json',
        '{"title": "最終タイトル", "tags": ["タグ1", "タグ2", "タグ3"]}',
        '```',
    ]
    return "\n".join(lines)


def _split_body_and_meta(text: str, idea: Idea, cfg: NoteAutoConfig) -> tuple[str, str, list[str]]:
    """生成テキストから本文・タイトル・タグを取り出す."""
    title = idea.title
    tags = list(cfg.default_tags)
    match = _META_RE.search(text)
    body = text
    if match:
        body = text[: match.start()].rstrip()
        try:
            meta = json.loads(match.group(1))
            title = meta.get("title") or title
            if meta.get("tags"):
                # 既定タグと生成タグをマージ（重複除去・順序維持）
                seen = set()
                tags = [
                    t for t in (list(meta["tags"]) + cfg.default_tags)
                    if not (t in seen or seen.add(t))
                ]
        except json.JSONDecodeError:
            pass
    return body, title, tags


def generate_article(
    cfg: NoteAutoConfig,
    idea: Idea,
    client: Optional[anthropic.Anthropic] = None,
) -> Article:
    """ネタ 1 本から記事を生成する."""
    client = client or anthropic.Anthropic()

    with client.messages.stream(
        model=cfg.model,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={"effort": cfg.effort},
        system=_system_prompt(cfg),
        messages=[{"role": "user", "content": _user_prompt(cfg, idea)}],
    ) as stream:
        message = stream.get_final_message()

    text = "".join(b.text for b in message.content if b.type == "text").strip()
    body, title, tags = _split_body_and_meta(text, idea, cfg)

    return Article(title=title, body=body, tags=tags, idea=idea)
