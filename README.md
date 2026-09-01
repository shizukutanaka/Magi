# Magi

世界の占術を横断的に試せる、完全無料のWebアプリケーションです。
ログイン不要・DBなしで、決定的な占術ドメイン層と参照用APIを提供します。

## 方針

- 8流派、全スプレッドを無条件で利用できます。
- 生年月日・氏名・問いは鑑定計算にのみ使用し、サーバに保存せず、ログにも出力しません。
- 濫用防止のため、鑑定APIにはIPアドレス単位のインメモリ・レートリミットだけを設けています。
- レートリミットの既定値は1分あたり60リクエストです。`MAGI_RATE_LIMIT_PER_MINUTE` で変更でき、0以下にすると無効になります。

## 技術スタック

- **Backend**: Python 3.12 / FastAPI / Pydantic v2
- **品質管理**: pytest / ruff
- **設計**: DB・ネットワーク・保存状態に依存しないステートレスな占術エンジン

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
レスポンスには計算に使った `seed` が含まれるため、同じ入力を用意すれば結果の再現性を検証できます。
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

起動後は `GET /health`、`GET /api/v1/systems`、`POST /api/v1/readings`、
`POST /api/v1/readings/daily` を利用できます。鑑定APIにはIPレートリミットが適用されますが、
`/health` には適用されません。

## Web UI

`uvicorn app.main:app` を起動した後、ブラウザで
`http://localhost:8000/` を開くと、今日の三賢者・鑑定・履歴を利用できます。
UIはHTML・CSS・ES Modulesだけで構成されており、ビルド工程、npm、`node_modules` は必要ありません。
フロントエンドも同じFastAPIプロセスから配信されるため、self-hostの起動方法は変わりません。

履歴はブラウザのlocalStorageにのみ保存され、画面からJSONとしてエクスポートまたは全削除できます。
サーバは履歴を含むリクエストデータを保存しません。

### 自分で結果を再現する

APIレスポンスの `seed` は、subject key・占術ID・対象日・問い・入力から決まります。
レスポンスの入力と `seed` を記録し、同じコードを自分の環境で実行することで、決定的な結果を検証できます。

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

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
