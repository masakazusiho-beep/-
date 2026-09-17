"""threads_auto — Threads（スレッズ）投稿の自動生成パイプライン.

お菓子作りのテーマで短い投稿文を毎日いくつか生成し、リポジトリに保存する。
既定は生成のみ（下書き）。Threads の認証情報を設定して --post を付けると、
公式 Graph API で自動投稿もできる。

- 生成は Claude API（軽量モデル既定）を使う。投稿は短いのでコストは小さい。
"""

from .config import ThreadsAutoConfig
from .models import Post

__all__ = ["ThreadsAutoConfig", "Post"]

__version__ = "0.1.0"
