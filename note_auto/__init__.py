"""note_auto — note.com 記事の自動化パイプライン.

ネタ収集 → 記事生成 → note への下書き投稿 → 定期実行 を一気通貫で行う。

- 記事生成は Claude API (claude-opus-4-8) を使う。
- note は公式投稿 API がないため、投稿は Playwright によるブラウザ自動操作。
  安全のためデフォルトは「下書き保存」まで（公開は人間が最終確認）。
"""

from .config import NoteAutoConfig
from .models import Idea, Article

__all__ = ["NoteAutoConfig", "Idea", "Article"]

__version__ = "0.1.0"
