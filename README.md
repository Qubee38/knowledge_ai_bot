# 汎用LLMチャットボットテンプレート

**バージョン**: 1.0.0  
**最終更新**: 2026年1月

---

## 📋 プロジェクト概要

このプロジェクトは、**設定ファイル（YAML）を編集するだけで異なるドメインのチャットボットに切り替えられる**汎用テンプレートです。

### 主な特徴

✅ **設定駆動設計** - YAMLファイル編集だけでドメイン切替  
✅ **スキーマ分離** - PostgreSQLスキーマでドメインごとにデータ分離  
✅ **動的ツールロード** - ドメインに応じてツールを自動読み込み  
✅ **簡単拡張** - 新ドメイン作成スクリプト完備  
✅ **ベストプラクティス** - モダンなPython/TypeScript実装  

### サンプルドメイン

- **horse-racing** - 競馬レース傾向分析ボット
- **customer-support** - カスタマーサポートボット

---

## 🚀 クイックスタート

### 前提条件

- Docker Desktop（最新版）
- Git
- OpenAI APIキー

### セットアップ（5分）

```bash
# 1. リポジトリクローン
git clone <your-repo-url>
cd knowledge-ai-bot

# 2. 環境変数設定
cp .env.example .env
vim .env
# OPENAI_API_KEY=sk-proj-your-key-here

# 3. Docker起動
docker-compose up -d

# 4. データベース初期化
./setup_db_from_scratch.sh

# 5. アクセス
# http://localhost:3000
```

---

## 🎯 ドメイン切替（1分）

### 現在のドメイン確認

```bash
cat config/app.config.yaml | grep active_domain
# active_domain: "horse-racing"
```

### ドメイン切替

```bash
# 1. app.config.yaml編集
vim config/app.config.yaml
# active_domain: "customer-support"  # ← 変更

# 2. 再起動
docker-compose restart backend

# 完了！
```

**たったこれだけで全く異なるドメインのボットに変身します。**

---

## 📁 プロジェクト構造

```
knowledge-ai-bot/
├── config/                         # 設定ファイル（核心）
│   ├── app.config.yaml            # アプリケーション設定
│   ├── agents.config.yaml         # エージェント基本設定
│   └── domains/                   # ドメイン別設定
│       ├── horse-racing/
│       │   ├── domain.yaml        # ドメイン設定
│       │   └── prompts.yaml       # プロンプト定義
│       └── customer-support/
│           ├── domain.yaml
│           └── prompts.yaml
│
├── frontend/                       # React + TypeScript
│   └── src/
│       ├── components/core/       # 汎用UIコンポーネント
│       └── hooks/                 # カスタムフック
│
├── backend/                        # FastAPI + Python
│   ├── app/
│   │   ├── core/                  # コアフレームワーク
│   │   │   ├── config.py         # ConfigLoader
│   │   │   ├── tool_loader.py    # ToolLoader
│   │   │   ├── agent_factory.py  # AgentFactory
│   │   │   └── db_utils.py       # DB接続（スキーマ対応）
│   │   └── domains/               # ドメイン実装
│   │       ├── horse_racing/
│   │       │   └── tools.py      # ドメイン固有ツール
│   │       └── customer_support/
│   │           └── tools.py
│   └── scripts/                   # ユーティリティ
│       └── parse_keibalab_text.py # データ投入
│
├── database/
│   └── schema/domains/            # スキーマ定義
│       └── horse_racing_schema.sql
│
├── scripts/
│   ├── create_domain.py           # 新ドメイン作成
│   └── setup_db_from_scratch.sh   # DB初期化
│
├── .env                            # 環境変数
├── docker-compose.yml              # Docker設定
└── README.md                       # このファイル
```

---

## 🔧 技術スタック

### バックエンド
- **FastAPI** - 高速Webフレームワーク
- **OpenAI Agents SDK** - マルチエージェント対応
- **PostgreSQL** - リレーショナルDB（スキーマ分離）
- **Redis** - キャッシュ・セッション管理
- **psycopg2** - PostgreSQLアダプタ

### フロントエンド
- **React 18** - UIライブラリ
- **TypeScript** - 型安全性
- **Vite** - 高速ビルドツール
- **react-markdown** - Markdown表示

### インフラ
- **Docker Compose** - コンテナオーケストレーション
- **PostgreSQL 16** - データベース
- **Redis 7** - キャッシュ

---

## 📚 ドキュメント

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - システムアーキテクチャ詳細
- **[DOMAIN_GUIDE.md](docs/DOMAIN_GUIDE.md)** - 新ドメイン追加ガイド
- **[DATABASE_GUIDE.md](docs/DATABASE_GUIDE.md)** - データベース設計
- **[CONFIGURATION_GUIDE.md](docs/CONFIGURATION_GUIDE.md)** - 設定ファイルリファレンス

---

## 🎓 使用例

### 1. 競馬分析ボット

```yaml
# config/app.config.yaml
active_domain: "horse-racing"
```

**機能:**
- レース傾向分析
- 人気別・枠順別統計
- 推奨馬選定

**クエリ例:**
- "シンザン記念の傾向を教えて"
- "有馬記念で狙うべき条件は？"

### 2. カスタマーサポートボット

```yaml
# config/app.config.yaml
active_domain: "customer-support"
```

**機能:**
- ナレッジベース検索
- サポートチケット作成
- 注文状況確認

**クエリ例:**
- "注文番号12345の配送状況は？"
- "返品方法を教えて"

---

## 🔄 ワークフロー

### 開発フロー

```
1. 新ドメイン作成
   ↓
2. domain.yaml編集
   ↓
3. ツール実装
   ↓
4. スキーマ作成
   ↓
5. データ投入
   ↓
6. テスト
```

### ドメイン切替フロー

```
1. app.config.yaml編集
   ↓
2. docker-compose restart
   ↓
3. 完了（10秒）
```

---

## 🐛 トラブルシューティング

### ポート競合

```bash
# ポート確認
lsof -i :3000
lsof -i :8000

# プロセス終了
kill -9 <PID>
```

### データベース接続エラー

```bash
# PostgreSQL確認
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot

# スキーマ確認
\dn

# テーブル確認
\dt horse_racing.*
```

### ログ確認

```bash
# すべてのログ
docker-compose logs -f

# 特定サービス
docker-compose logs -f backend
docker-compose logs -f frontend
```

---

**Happy Coding! 🎉**