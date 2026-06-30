"""note への投稿: Playwright によるブラウザ自動操作.

note は公式の投稿 API を公開していないため、ログイン→新規テキスト記事→
タイトル/本文入力→**下書き保存** という人間の操作を自動化する。

⚠️ 重要な注意:
- note の UI（DOM/セレクタ）は予告なく変わる。動かなくなったらセレクタの更新が必要。
- 自動操作は note の利用規約に抵触する可能性がある。**自分のアカウントの下書き保存に
  限定**し、公開は人間が最終確認する運用を強く推奨する（既定は下書き保存）。
- ログイン情報は環境変数で渡し、コードやリポジトリに残さない。

Playwright が未インストールでも他モジュールが import できるよう、依存は関数内で読む。
"""

from __future__ import annotations

import pathlib
from typing import Optional

from .config import NoteAutoConfig
from .models import Article

NOTE_LOGIN_URL = "https://note.com/login"
NOTE_NEW_NOTE_URL = "https://note.com/notes/new"


class PublishResult:
    """投稿結果."""

    def __init__(self, ok: bool, url: Optional[str] = None, detail: str = ""):
        self.ok = ok
        self.url = url
        self.detail = detail

    def __repr__(self) -> str:  # pragma: no cover
        return f"PublishResult(ok={self.ok}, url={self.url!r}, detail={self.detail!r})"


def publish_to_note(cfg: NoteAutoConfig, article: Article) -> PublishResult:
    """記事を note に投稿（既定は下書き保存）する.

    `cfg.publish` が True のときのみ公開を試みる。
    """
    cfg.require_credentials()
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise RuntimeError(
            "Playwright が必要です: pip install playwright && playwright install chromium"
        ) from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=cfg.headless)
        context = browser.new_context()
        page = context.new_page()
        try:
            _login(page, cfg)
            _open_new_note(page)
            _fill_article(page, article)
            url = _save(page, publish=cfg.publish)
            mode = "公開" if cfg.publish else "下書き保存"
            return PublishResult(ok=True, url=url, detail=f"{mode}しました")
        except PWTimeout as exc:
            return PublishResult(ok=False, detail=f"操作がタイムアウト: {exc}")
        finally:
            context.close()
            browser.close()


def _login(page, cfg: NoteAutoConfig) -> None:
    page.goto(NOTE_LOGIN_URL, wait_until="domcontentloaded")
    # メール/パスワード欄は name 属性が安定している傾向。だめなら type で代替。
    email = page.locator("input[name='email'], input[type='email']").first
    email.fill(cfg.note_email)
    pw = page.locator("input[name='password'], input[type='password']").first
    pw.fill(cfg.note_password)
    page.get_by_role("button", name="ログイン").first.click()
    page.wait_for_load_state("networkidle")


def _open_new_note(page) -> None:
    page.goto(NOTE_NEW_NOTE_URL, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")


def _fill_article(page, article: Article) -> None:
    # タイトル: プレースホルダ「記事タイトル」の textarea が定番。
    title = page.locator(
        "textarea[placeholder*='タイトル'], [aria-label*='タイトル']"
    ).first
    title.click()
    title.fill(article.title)

    # 本文: contenteditable な本文エディタにフォーカスして入力。
    body = page.locator("div[contenteditable='true']").first
    body.click()
    body.type(article.body)


def _save(page, publish: bool) -> Optional[str]:
    """下書き保存（既定）または公開を行い、可能なら記事 URL を返す."""
    if publish:
        # 「公開設定」→「投稿する」の二段。UI 変更に弱いので text で広めに拾う。
        page.get_by_role("button", name="公開に進む").first.click()
        page.get_by_role("button", name="投稿する").first.click()
    else:
        page.get_by_role("button", name="下書き保存").first.click()
    page.wait_for_load_state("networkidle")
    return page.url


def save_locally(cfg: NoteAutoConfig, article: Article) -> pathlib.Path:
    """投稿せず、ローカルに下書きを保存する（ドライラン用）."""
    return article.save(cfg.output_dir)
