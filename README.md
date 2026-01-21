# Keiba-Knowledge AI

**汎用LLMチャットボットテンプレート × 競馬ナレッジボット**

## 🎯 プロジェクト概要

- **テンプレート性**: 設定駆動で他ドメインに転用可能
- **実用性**: 競馬レース傾向分析とデータドリブン推奨
- **技術スタック**: FastAPI + OpenAI + PostgreSQL + React

## 🚀 クイックスタート

### 前提条件

- Docker & Docker Compose
- OpenAI APIキー

### セットアップ
```bash
# 1. リポジトリクローン
git clone <repository-url>
cd keiba-knowledge-ai

# 2. 環境変数設定
cp .env.example .env
# .envを編集してOPENAI_API_KEYを設定

# 3. Docker起動
docker-compose up -d

# 4. 動作確認
curl http://localhost:8000/
```

### 確認エンドポイント

- **ルート**: http://localhost:8000/
- **ヘルスチェック**: http://localhost:8000/api/health
- **設定確認**: http://localhost:8000/api/config
- **ドメイン設定**: http://localhost:8000/api/config/domain

## 📁 プロジェクト構造
```
keiba-knowledge-ai/
├── backend/           # FastAPI バックエンド
├── frontend/          # React フロントエンド
├── config/            # 設定ファイル（YAML）
├── database/          # データベーススキーマ・シード
├── scripts/           # ユーティリティスクリプト
└── docs/              # ドキュメント
```

## 🛠️ 開発ステータス

- [x] Phase 1: プロジェクト初期化
- [x] Phase 2: 設定システム
- [x] Phase 3: FastAPI基本構成
- [x] Phase 4: エージェント統合
- [x] Phase 5: データベース統合
- [x] Phase 6: フロントエンド実装

## 📝 ライセンス

MIT License