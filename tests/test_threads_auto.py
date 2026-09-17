"""threads_auto のテスト。Claude API はフェイクで差し替えて検証する。"""

from __future__ import annotations

import json
from types import SimpleNamespace

from threads_auto.config import ThreadsAutoConfig, DEFAULT_MODEL
from threads_auto.generate import _build_prompt, _extract_json, generate_posts
from threads_auto.models import Post
from threads_auto.pipeline import collect_past_posts, run_pipeline


def _text_block(text):
    return SimpleNamespace(type="text", text=text)


class FakeMessages:
    def __init__(self, create_text):
        self._create_text = create_text
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(content=[_text_block(self._create_text)])


class FakeClient:
    def __init__(self, create_text):
        self.messages = FakeMessages(create_text)


# ---------- config ----------

def test_config_defaults_and_toml(tmp_path):
    cfg = ThreadsAutoConfig.load(None)
    assert cfg.model == DEFAULT_MODEL
    assert cfg.max_chars == 500

    p = tmp_path / "t.toml"
    p.write_text(
        '[content]\ntheme="お菓子"\nmax_chars=300\npage_url="https://x/"\n'
        '[generation]\nmodel="m"\n[threads]\npublish=true\n',
        encoding="utf-8",
    )
    cfg = ThreadsAutoConfig.load(p)
    assert cfg.theme == "お菓子"
    assert cfg.max_chars == 300
    assert cfg.page_url == "https://x/"
    assert cfg.model == "m"
    assert cfg.publish is True


def test_env_overrides_credentials(monkeypatch):
    monkeypatch.setenv("THREADS_USER_ID", "123")
    monkeypatch.setenv("THREADS_TOKEN", "tok")
    cfg = ThreadsAutoConfig.load(None)
    assert cfg.threads_user_id == "123"
    assert cfg.threads_token == "tok"
    cfg.require_credentials()  # 揃っていれば例外なし


# ---------- prompt ----------

def test_build_prompt_includes_page_url_and_avoid():
    cfg = ThreadsAutoConfig(theme="お菓子", page_url="https://shop/")
    p = _build_prompt(cfg, 3, avoid=["前の投稿A"])
    assert "https://shop/" in p
    assert "前の投稿A" in p
    assert "500 文字以内" in p


def test_build_prompt_without_url_says_profile():
    p = _build_prompt(ThreadsAutoConfig(), 2)
    assert "プロフィールのリンク" in p


# ---------- extract / generate ----------

def test_extract_json_from_noise():
    assert _extract_json('前置き {"posts": ["a"]} 後ろ') == {"posts": ["a"]}


def test_generate_posts_parses_and_clips():
    payload = json.dumps({"posts": ["みじかい投稿", "  ", "x" * 800]})
    cfg = ThreadsAutoConfig(max_chars=100)
    posts = generate_posts(cfg, count=3, client=FakeClient(payload))
    # 空白だけの投稿は除外され、長すぎるものは max_chars に切り詰められる
    assert len(posts) == 2
    assert posts[0].text == "みじかい投稿"
    assert len(posts[1].text) == 100


def test_generate_posts_accepts_object_items():
    payload = json.dumps({"posts": [{"text": "オブジェクト形式でもOK"}]})
    posts = generate_posts(ThreadsAutoConfig(), client=FakeClient(payload))
    assert posts[0].text == "オブジェクト形式でもOK"


# ---------- models ----------

def test_post_save_writes_file(tmp_path):
    path = Post(text="ほんぶん").save(tmp_path, index=1)
    assert path.exists()
    assert path.read_text(encoding="utf-8").strip() == "ほんぶん"


# ---------- pipeline ----------

def test_collect_past_posts_reads_first_lines(tmp_path):
    (tmp_path / "2026-01-01-000000-0.md").write_text("いちばん上の行\n2行目", encoding="utf-8")
    got = collect_past_posts(str(tmp_path), str(tmp_path / "missing"))
    assert got == ["いちばん上の行"]


def test_run_pipeline_generates_and_saves(tmp_path):
    payload = json.dumps({"posts": ["投稿1", "投稿2"]})
    cfg = ThreadsAutoConfig(output_dir=str(tmp_path / "out"))
    result = run_pipeline(cfg, count=2, dry_run=True, client=FakeClient(payload))
    assert len(result.posts) == 2
    assert len(result.saved) == 2
    assert not result.published  # dry_run では投稿しない
    for path in result.saved:
        assert (tmp_path / "out").exists()
