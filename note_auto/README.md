# note_auto — note 記事の自動化パイプライン

**ネタ収集 → 記事生成 → note への投稿 → 定期実行** を一気通貫で行うツールです。

- 記事生成は **Claude API（`claude-opus-4-8`）** を使用。
- note は公式の投稿 API がないため、投稿は **Playwright によるブラウザ自動操作**。
- 安全側の設計：**既定は「下書き保存」まで**（公開は人間が最終確認）。

```
ネタ収集(ideas.py) → 記事生成(generate.py) → 投稿(publish.py)
        └─────────── オーケストレーション(pipeline.py) ───────────┘
                                定期実行: .github/workflows/note-auto.yml
```

## セットアップ

```bash
pip install -e ".[note]"
playwright install chromium          # note へ投稿する場合のみ

cp examples/note_config.example.toml note_config.toml   # 編集して使う
```

機密情報は環境変数で渡します（リポジトリには置かない）:

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # 記事生成
export NOTE_EMAIL=you@example.com     # note 投稿（任意）
export NOTE_PASSWORD=********           # note 投稿（任意）
```

## 使い方

```bash
# 1. ネタ出し（--research で web 検索を使い最新トレンドを反映）
python -m note_auto ideas --config note_config.toml --count 5 --research

# 2. タイトル指定で 1 本生成（drafts/ に保存）
python -m note_auto generate --config note_config.toml --title "AIで時短する個人開発術"

# 3. フルパイプライン（既定はドライラン = ローカル保存のみ）
python -m note_auto run --config note_config.toml --count 1 --research

# 4. note へ下書き保存まで自動化
python -m note_auto run --config note_config.toml --count 1 --post

# 5. 公開まで自動化（自己責任で）
python -m note_auto run --config note_config.toml --count 1 --post --publish
```

## 定期実行

`.github/workflows/note-auto.yml` が毎週月曜に生成を実行します（既定はドライラン、
成果物は Artifact として保存）。`ANTHROPIC_API_KEY`（投稿まで行うなら `NOTE_EMAIL` /
`NOTE_PASSWORD` も）を GitHub Secrets に登録してください。ローカルで回すなら `cron` で
同じコマンドを叩けば十分です。

## 注意事項

- **note の利用規約**：ブラウザ自動操作はアカウント停止などのリスクがあります。
  自分のアカウントでの下書き保存に留め、公開は人手で確認する運用を推奨します。
- **UI 変更への弱さ**：`publish.py` の DOM セレクタは note の画面変更で動かなくなる
  ことがあります。その場合はセレクタの更新が必要です。
- **生成物のレビュー**：AI 生成記事はそのまま公開せず、事実確認と推敲を必ず行ってください。
- 生成記事・`note_config.toml` は `.gitignore` 済み（機密が混入しないように）。
