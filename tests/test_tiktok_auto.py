"""tiktok_auto のテスト（Claude/ffmpeg/TTS に依存しない純ロジック中心）。"""

from __future__ import annotations

import json
from types import SimpleNamespace

from tiktok_auto.config import TikTokConfig, DEFAULT_MODEL
from tiktok_auto.models import VideoScript, Scene, slugify
from tiktok_auto.render import wrap_text
from tiktok_auto.script import parse_script, generate_script


def test_config_loads_theme_from_content(tmp_path):
    toml = tmp_path / "c.toml"
    toml.write_text(
        '[content]\ntheme = "お菓子"\nkeywords = ["製菓"]\n[tiktok]\nvoice = "ja-JP-KeitaNeural"\n',
        encoding="utf-8",
    )
    cfg = TikTokConfig.load(toml)
    assert cfg.theme == "お菓子"
    assert cfg.keywords == ["製菓"]
    assert cfg.voice == "ja-JP-KeitaNeural"
    assert cfg.model == DEFAULT_MODEL


def test_wrap_text_breaks_by_max_chars():
    assert wrap_text("あいうえおかきくけこ", 5) == ["あいうえお", "かきくけこ"]
    assert wrap_text("", 5) == [""]


def test_slugify():
    assert slugify("失敗しない/コツ?") == "失敗しない-コツ"


def test_parse_script():
    payload = {
        "hook": "知らないと損！",
        "scenes": [
            {"onscreen": "ポイント1", "narration": "まず計量が大事です。"},
            {"onscreen": "ポイント2", "narration": "次に温度です。"},
        ],
        "caption": "保存版！",
        "hashtags": ["お菓子作り", "製菓"],
    }
    s = parse_script(json.dumps(payload, ensure_ascii=False))
    assert s.hook == "知らないと損！"
    assert len(s.scenes) == 2
    assert s.hashtags == ["お菓子作り", "製菓"]


def test_all_scenes_prepends_hook():
    s = VideoScript(hook="フック", scenes=[Scene("A", "a"), Scene("B", "b")], caption="c")
    scenes = s.all_scenes()
    assert len(scenes) == 3
    assert scenes[0].onscreen == "フック"


def test_caption_text_includes_hashtags():
    s = VideoScript(hook="h", scenes=[], caption="本文", hashtags=["x", "y"])
    text = s.caption_text()
    assert "本文" in text
    assert "#x #y" in text


def test_save_sidecar(tmp_path):
    s = VideoScript(hook="フック", scenes=[Scene("A", "a")], caption="c", hashtags=["t"])
    stem = VideoScript.default_stem(s.hook)
    txt = s.save_sidecar(tmp_path, stem)
    assert txt.exists()
    data = json.loads((tmp_path / f"{stem}.json").read_text(encoding="utf-8"))
    assert data["hook"] == "フック"


def test_generate_script_with_fake_client():
    payload = {
        "hook": "H",
        "scenes": [{"onscreen": "O", "narration": "N"}],
        "caption": "C",
        "hashtags": ["t1"],
    }

    class FakeMessages:
        def create(self, **kwargs):
            block = SimpleNamespace(type="text", text=json.dumps(payload, ensure_ascii=False))
            return SimpleNamespace(content=[block])

    class FakeClient:
        messages = FakeMessages()

    s = generate_script(TikTokConfig(theme="t"), client=FakeClient())
    assert s.hook == "H"
    assert s.scenes[0].onscreen == "O"
