# threads_auto — Threads 投稿の自動生成

お菓子作りのテーマで、Threads（スレッズ）向けの短い投稿文を毎日いくつか生成し、
リポジトリの `threads/` に保存します。気に入ったものをコピーして貼るだけ。

- **既定は「下書き生成」のみ**（安全）。生成された投稿は GitHub の `threads/` フォルダに入り、
  お知らせ（Issue）で通知されます。
- 投稿文は短いので、**コストは小さめ**（軽量モデルを既定に使用）。
- 設定は `threads_config.toml`（テーマ・誘導先URLなど）を GitHub 上で編集できます。

## 使い方（ローカル）

```bash
pip install -e ".[threads-auto]"
export ANTHROPIC_API_KEY=...      # 生成に必要
python -m threads_auto run --config threads_config.toml --count 3
```

生成物は `threads-drafts/` に `.md` で保存されます。

## 自動実行

`.github/workflows/threads-auto.yml` が毎朝 6:00 JST に実行し、`threads/` に
コミット＋通知します。手動実行（workflow_dispatch）も可能です。

## Threads へ自動投稿する（任意・上級）

下書きでなく実際に自動投稿したい場合：

1. Meta で Threads API アプリを作成し、対象アカウントの
   **THREADS_USER_ID** と長期 **THREADS_TOKEN** を取得
2. それらをリポジトリの **Secrets** に登録
3. `threads_config.toml` の `[threads] publish = true` にする
   （またはワークフローの `--post` 付きステップを有効化）

投稿は公式 Graph API（`threads_auto/poster.py`）を使い、標準ライブラリのみで動きます。
