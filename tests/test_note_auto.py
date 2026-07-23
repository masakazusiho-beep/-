"""note_auto のテスト。Claude API はフェイクで差し替えて検証する。"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from note_auto.config import NoteAutoConfig, DEFAULT_MODEL
from note_auto.generate import _split_body_and_meta, _user_prompt, generate_article
from note_auto.ideas import _extract_json, _build_prompt, generate_ideas
from note_auto.models import Article, Idea, _slugify
from note_auto.pipeline import collect_past_titles


# ---------- フェイクの Claude クライアント ----------

def _text_block(text):
    return SimpleNamespace(type="text", text=text)


class _FakeStream:
    def __init__(self, message):
        self._message = message

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        return self._message


class FakeMessages:
    def __init__(self, create_text=None, stream_text=None):
        self._create_text = create_text
        self._stream_text = stream_text

    def create(self, **kwargs):
        return SimpleNamespace(content=[_text_block(self._create_text)])

    def stream(self, **kwargs):
        return _FakeStream(SimpleNamespace(content=[_text_block(self._stream_text)]))


class FakeClient:
    def __init__(self, create_text=None, stream_text=None):
        self.messages = FakeMessages(create_text, stream_text)


# ---------- models ----------

def test_slugify_handles_symbols():
    assert _slugify("a/b:c?") == "a-b-c"
    assert _slugify("   ") == "untitled"


def test_article_save_writes_markdown_and_json(tmp_path):
    art = Article(title="テスト記事", body="本文です。", tags=["AI", "自動化"])
    md = art.save(tmp_path)
    assert md.exists()
    content = md.read_text(encoding="utf-8")
    assert content.startswith("# テスト記事")
    assert "#AI #自動化" in content
    # JSON サイドカーも書かれる
    sidecar = md.with_suffix(".json")
    assert sidecar.exists()
    assert json.loads(sidecar.read_text(encoding="utf-8"))["title"] == "テスト記事"


# ---------- config ----------

def test_config_defaults():
    cfg = NoteAutoConfig.load()
    assert cfg.model == DEFAULT_MODEL
    assert cfg.publish is False


def test_config_from_toml_and_env(tmp_path, monkeypatch):
    toml = tmp_path / "c.toml"
    toml.write_text(
        '[content]\ntheme = "テーマA"\n[note]\npublish = true\n', encoding="utf-8"
    )
    monkeypatch.setenv("NOTE_EMAIL", "me@example.com")
    monkeypatch.setenv("NOTE_PASSWORD", "secret")
    cfg = NoteAutoConfig.load(toml)
    assert cfg.theme == "テーマA"
    assert cfg.publish is True
    assert cfg.note_email == "me@example.com"


def test_require_credentials_raises_when_missing(monkeypatch):
    monkeypatch.delenv("NOTE_EMAIL", raising=False)
    monkeypatch.delenv("NOTE_PASSWORD", raising=False)
    cfg = NoteAutoConfig()
    with pytest.raises(RuntimeError):
        cfg.require_credentials()


# ---------- ideas ----------

def test_extract_json_from_noisy_text():
    text = 'ここに提案です:\n{"ideas": [{"title": "x"}]}\nどうぞ。'
    assert _extract_json(text)["ideas"][0]["title"] == "x"


def test_build_prompt_includes_avoid_titles():
    p = _build_prompt(NoteAutoConfig(theme="お菓子"), count=3, research=False,
                      avoid_titles=["既出タイトルA", "既出タイトルB"])
    assert "既出タイトルA" in p
    assert "かぶらない" in p
    # カテゴリ分散の指示も入る
    assert "カテゴリ" in p


def test_collect_past_titles(tmp_path):
    (tmp_path / "2026-01-01-foo.md").write_text("# 記事タイトル1\n\n本文", encoding="utf-8")
    (tmp_path / "2026-01-02-bar.md").write_text("# 記事タイトル2\n\n本文", encoding="utf-8")
    titles = collect_past_titles(str(tmp_path), str(tmp_path / "missing"))
    assert titles == ["記事タイトル1", "記事タイトル2"]


def test_generate_ideas_structured():
    payload = {
        "ideas": [
            {"title": "T1", "angle": "A1", "keywords": ["k1"], "rationale": "r1"},
            {"title": "T2", "angle": "A2", "keywords": ["k2", "k3"], "rationale": "r2"},
        ]
    }
    client = FakeClient(create_text=json.dumps(payload, ensure_ascii=False))
    ideas = generate_ideas(NoteAutoConfig(theme="t"), count=2, client=client)
    assert [i.title for i in ideas] == ["T1", "T2"]
    assert ideas[1].keywords == ["k2", "k3"]


# ---------- generate ----------

def test_split_body_and_meta_parses_trailing_json():
    cfg = NoteAutoConfig(default_tags=["既定"])
    idea = Idea(title="元タイトル")
    text = (
        "## 見出し\n本文本文。\n\n"
        '```json\n{"title": "最終タイトル", "tags": ["A", "B"]}\n```'
    )
    body, title, tags = _split_body_and_meta(text, idea, cfg)
    assert title == "最終タイトル"
    assert "```json" not in body
    assert tags == ["A", "B", "既定"]


def test_split_body_and_meta_without_meta_uses_defaults():
    cfg = NoteAutoConfig(default_tags=["既定"])
    idea = Idea(title="元タイトル")
    body, title, tags = _split_body_and_meta("本文のみ。", idea, cfg)
    assert title == "元タイトル"
    assert tags == ["既定"]


def test_paid_prompt_includes_paywall_instructions():
    idea = Idea(title="ネタ")
    assert "🔒" not in _user_prompt(NoteAutoConfig(paid=False), idea)
    paid = _user_prompt(NoteAutoConfig(paid=True), idea)
    assert "🔒" in paid
    assert "有料" in paid


def test_generate_article_end_to_end():
    cfg = NoteAutoConfig()
    idea = Idea(title="ネタ", keywords=["k"])
    stream_text = '記事本文です。\n\n```json\n{"title": "完成", "tags": ["t1"]}\n```'
    client = FakeClient(stream_text=stream_text)
    art = generate_article(cfg, idea, client=client)
    assert art.title == "完成"
    assert art.body == "記事本文です。"
    assert art.tags == ["t1"]
    assert art.idea is idea
