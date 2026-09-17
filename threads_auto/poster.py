"""Threads へ投稿する（任意機能）.

Threads の公式 Graph API を使う。THREADS_USER_ID と THREADS_TOKEN が必要。
依存を増やさないよう標準ライブラリ（urllib）だけで実装している。

参考: https://developers.facebook.com/docs/threads
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass

_BASE = "https://graph.threads.net/v1.0"


@dataclass
class PostResult:
    ok: bool
    detail: str = ""
    permalink: str = ""


def _post_form(url: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (信頼できる固定ホスト)
        return json.loads(resp.read().decode("utf-8"))


def post_text(user_id: str, token: str, text: str) -> PostResult:
    """テキスト投稿を作成して公開する（2 ステップ）."""
    try:
        created = _post_form(
            f"{_BASE}/{user_id}/threads",
            {"media_type": "TEXT", "text": text, "access_token": token},
        )
        creation_id = created.get("id")
        if not creation_id:
            return PostResult(False, f"creation_id が取得できませんでした: {created}")
        published = _post_form(
            f"{_BASE}/{user_id}/threads_publish",
            {"creation_id": creation_id, "access_token": token},
        )
        pid = published.get("id", "")
        return PostResult(True, f"published id={pid}", "")
    except Exception as e:  # pragma: no cover - ネットワーク依存
        return PostResult(False, f"投稿に失敗しました: {e}")
