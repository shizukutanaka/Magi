# コントリビューションガイド

## 開発環境

バックエンドの仮想環境を作成し、依存関係をインストールして起動します。

```bash
cd backend
uv venv
source .venv/bin/activate
pip install -r requirements.txt pytest httpx ruff
uvicorn app.main:app --reload --no-proxy-headers
```

## 必ず守るルール

### 決定性

同じ入力（subject key・日付・問い・生年月日・氏名・オプション）は常に同じ結果を返してください。
シードに表示言語を入れないでください。抽選は翻訳済み文字列ではなく安定キーに対して行ってください。
既存の解釈データの行順や重みを変えないでください。過去の共有URLの再現が壊れます。

### 流派の追加

`app/divination/engines/<name>.py` に `cast(input, rng, lang) -> Reading` を実装し、レジストリに登録します。
`app/divination/data/` に日本語データ、`data/en/` に英訳を置き、テストを追加してください。

### 翻訳の追加

日本語データが唯一のソースです。`data/en/` に安定キーで訳を置いてください。
`pytest` の網羅テストが通れば、`interpretation_langs` の申告は自動で変わります。
手書きの一覧はありません。

## PR前チェック

```bash
cd backend
source .venv/bin/activate
python -m ruff check app tests
python -m pytest -q
```

秘密情報や `.env` をコミットしないでください。詳細は `SECURITY.md` を参照してください。
