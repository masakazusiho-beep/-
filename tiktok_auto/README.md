# tiktok_auto — 顔出しなしショート動画の自動生成

**台本生成 → ナレーション → テロップ動画の組み立て** を自動化し、TikTok/Reels/Shorts 向けの
縦型 MP4 を作ります。投稿はできあがった動画を手動でアップロードします。

```
台本(Claude) → ナレーション(edge-tts/無料) → テロップ画像(Pillow) → 動画(ffmpeg)
```

## 仕組み

- **台本**：Claude（`claude-opus-4-8`）が「フック＋各シーンのテロップ＋ナレーション＋キャプション＋ハッシュタグ」を生成
- **音声**：`edge-tts`（Microsoft の無料音声、APIキー不要）で日本語ナレーション
- **動画**：各シーンを「背景＋テロップ画像＋音声」で作り、`ffmpeg` で1本に結合（縦型 1080×1920）
- テーマは `note_config.toml` の `[content]` を共有。声や色は `[tiktok]` セクションで調整可

## クラウドで使う（GitHub Actions）

`.github/workflows/tiktok-auto.yml` の「Run workflow」ボタンで動画を生成 →
`videos/` に保存され、完成のお知らせ（通知）が届きます。

毎日自動にしたいときは、ワークフロー内の `schedule` のコメントを外してください。

## 手元で使う（要 ffmpeg）

```bash
# 準備（Mac は: brew install ffmpeg）
pip install -e ".[tiktok]"

# 台本だけ確認
python -m tiktok_auto script --config note_config.toml

# 動画を1本作る（videos/ に MP4 と キャプション.txt ができる）
python -m tiktok_auto make --config note_config.toml --verbose
```

## 設定（note_config.toml の任意セクション）

```toml
[tiktok]
target_seconds = 30          # 動画の長さの目安
voice = "ja-JP-NanamiNeural" # 声（"ja-JP-KeitaNeural" は男性）
speech_rate = "+0%"          # "+10%" で少し速く
bg_color = "#111827"         # 背景色
text_color = "#FFFFFF"       # 文字色
```

## 注意

- 動画の見た目はシンプルな「背景＋テロップ＋ナレーション」です（凝った編集や実写ではありません）。
- BGM は著作権に配慮し既定では入れていません。付けたい場合はフリー音源を別途用意してください。
- TikTok への自動投稿は規約・安定性の面から行いません（できた動画を手動アップ）。
