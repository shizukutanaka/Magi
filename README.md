# Magi

世界の占術を横断的に試せる、月額サブスクリプション型Webアプリケーションです。
第1フェーズでは、DB・認証・課金・フロントエンドに先立つ、決定的な占術ドメイン層と参照用APIを提供します。

## 技術スタック

- **Backend**: Python 3.12 / FastAPI / Pydantic v2
- **品質管理**: pytest / ruff / GitHub Actions
- **設計**: DB・ネットワーク・現在時刻に依存しない純粋な占術エンジン

## 収録占術

| ID | 名称 | 伝統 | 必要入力 |
| --- | --- | --- | --- |
| `tarot` | タロット | 西洋 | なし |
| `iching` | 易経（周易） | 中国 | なし |
| `runes` | ルーン | 北欧 | なし |
| `omikuji` | おみくじ | 日本 | なし |
| `astrology` | 西洋占星術 | 西洋 | 生年月日 |
| `numerology` | 数秘術 | 西洋（ピタゴラス） | 氏名・生年月日 |
| `bazi` | 干支・四柱推命（略式） | 中国 | 生年月日 |
| `mayan` | マヤ暦ツォルキン | 中米 | 生年月日 |

同じ利用者・対象日・問い・入力であれば、`generated_at` を除いて同じ結果を返します。
数秘術では ASCII 英字にピタゴラス式（A=1〜I=9の循環）を適用します。日本語などの非ASCII文字は
NFKC正規化後、Unicodeコードポイント `% 9 + 1` で数値化します。
マヤ暦は GMT 相関定数 584283 と、日付をユリウス日へ変換して260日周期に還元する簡略方式です。
干支・四柱推命は年柱・日柱を用いる略式鑑定であり、完全な命式ではありません。

## 起動

```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
uvicorn app.main:app --reload
```

`GET /health`、`GET /api/v1/systems`、`POST /api/v1/readings`、
`POST /api/v1/readings/daily` を利用できます。P1では `X-Magi-Tier: free|plus|pro`
ヘッダーを仮のティア依存関数として使用します。

## テスト

```bash
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt pytest httpx ruff
python -m ruff check app tests
python -m pytest -q
```

## 免責

本鑑定はエンターテインメントおよび内省の補助を目的とし、医療・法律・投資の助言ではありません。
