# 新ドメイン追加ガイド

**バージョン**: 1.0.0  
**最終更新**: 2026年1月

---

## 📋 目次

1. [クイックスタート](#クイックスタート)
2. [手動作成手順](#手動作成手順)
3. [設定ファイル詳細](#設定ファイル詳細)
4. [ツール実装](#ツール実装)
5. [データベーススキーマ](#データベーススキーマ)
6. [テスト](#テスト)
7. [トラブルシューティング](#トラブルシューティング)

---

## クイックスタート

### 自動作成スクリプト使用（推奨）

```bash
# 新ドメイン作成
python scripts/create_domain.py e-commerce "ECサイトボット"

# 生成されたファイル確認
ls config/domains/e-commerce/
# domain.yaml  prompts.yaml

ls backend/app/domains/e_commerce/
# __init__.py  tools.py
```

**生成されるファイル:**
1. `config/domains/e-commerce/domain.yaml`
2. `config/domains/e-commerce/prompts.yaml`
3. `backend/app/domains/e_commerce/__init__.py`
4. `backend/app/domains/e_commerce/tools.py`

---

## 手動作成手順

自動スクリプトを使わずに手動で作成する場合の完全ガイドです。

### Step 1: ディレクトリ作成

```bash
# 設定ディレクトリ
mkdir -p config/domains/my-domain

# バックエンドディレクトリ
mkdir -p backend/app/domains/my_domain
```

**注意:** ドメインIDは `kebab-case`、Pythonモジュールは `snake_case`

---

### Step 2: domain.yaml 作成

**ファイル:** `config/domains/my-domain/domain.yaml`

```yaml
# ドメイン基本情報
domain:
  id: "my-domain"
  name: "マイドメインボット"
  description: "マイドメインの説明"
  version: "1.0.0"
  author: "あなたの名前"

# エージェント設定
agent:
  name: "MyDomainAgent"
  model: "gpt-4o"
  temperature: 0.7
  max_tokens: 4000
  
  # 使用するプロンプトキー
  prompt_templates:
    - "domain_instructions"
    - "key_principles"

# 使用するツール
tools:
  enabled:
    - "my_tool_function"
    - "another_tool_function"

# データベース設定
database:
  # スキーマ名（推奨: ドメインIDのsnake_case版）
  schema: "my_domain"
  
  # スキーマ分離を使用するか
  use_schema_separation: true

# UI設定
ui:
  # テーマカラー
  theme:
    primary: "#4A90E2"
    secondary: "#50C878"
    accent: "#FF6B6B"
  
  # クイックアクション
  quick_actions:
    - label: "サンプルクエリ1"
      query: "これはサンプルクエリです"
      icon: "🎯"
    
    - label: "サンプルクエリ2"
      query: "もう一つのサンプル"
      icon: "📊"
  
  # サンプルクエリ
  sample_queries:
    - "質問例1"
    - "質問例2"
    - "質問例3"
```

---

### Step 3: prompts.yaml 作成

**ファイル:** `config/domains/my-domain/prompts.yaml`

```yaml
# ドメイン固有プロンプト

# ドメイン固有指示
domain_instructions: |
  あなたは[ドメイン名]の専門家です。
  
  ## 役割
  - [役割1]
  - [役割2]
  
  ## 対応範囲
  - [対応範囲1]
  - [対応範囲2]

# 重要な原則
key_principles: |
  ## 原則
  1. [原則1]
  2. [原則2]
  3. [原則3]

# 応答フォーマット
output_format: |
  ## 応答形式
  
  ### 1. [セクション1]
  [説明]
  
  ### 2. [セクション2]
  [説明]

# その他のプロンプトテンプレート
additional_template: |
  必要に応じて追加のテンプレートを定義
```

---

### Step 4: ツール実装

**ファイル:** `backend/app/domains/my_domain/tools.py`

```python
"""
マイドメイン固有ツール
"""
from typing import List, Dict, Any
from app.core.db_utils import get_db_connection_for_domain


def my_tool_function(param1: str, param2: int = 10) -> List[Dict[str, Any]]:
    """
    ツールの説明
    
    Args:
        param1: パラメータ1の説明
        param2: パラメータ2の説明（デフォルト: 10）
    
    Returns:
        結果のリスト
    
    Example:
        >>> my_tool_function("test", 5)
        [{'key': 'value'}]
    """
    # データベース接続（スキーマ自動設定）
    conn = get_db_connection_for_domain()
    cursor = conn.cursor()
    
    try:
        # クエリ実行
        cursor.execute("""
            SELECT *
            FROM my_table
            WHERE column1 = %s
            LIMIT %s
        """, (param1, param2))
        
        # 結果取得
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return results
    
    finally:
        conn.close()


def another_tool_function(query: str) -> Dict[str, Any]:
    """
    別のツールの説明
    
    Args:
        query: クエリ文字列
    
    Returns:
        処理結果
    """
    # 処理ロジック
    result = {
        "status": "success",
        "data": f"処理結果: {query}"
    }
    
    return result
```

**ツール実装のベストプラクティス:**

✅ **docstring必須** - GPTがツールを理解するため  
✅ **型ヒント** - 引数・戻り値の型を明示  
✅ **エラーハンドリング** - try-finallyで確実にクローズ  
✅ **接続管理** - `get_db_connection_for_domain()` 使用  

---

### Step 5: `__init__.py` 作成

**ファイル:** `backend/app/domains/my_domain/__init__.py`

```python
"""
マイドメイン

ドメイン概要:
- [機能1]
- [機能2]
"""

__version__ = "1.0.0"
```

---

### Step 6: データベーススキーマ作成

**ファイル:** `database/schema/domains/my_domain_schema.sql`

```sql
-- マイドメインスキーマ
-- データベース: knowledge_ai_bot
-- スキーマ: my_domain

-- スキーマ作成
CREATE SCHEMA IF NOT EXISTS my_domain;

-- 検索パス設定
SET search_path TO my_domain, public;

-- テーブル1
CREATE TABLE IF NOT EXISTS my_domain.my_table (
    id SERIAL PRIMARY KEY,
    column1 VARCHAR(200) NOT NULL,
    column2 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- テーブル2
CREATE TABLE IF NOT EXISTS my_domain.another_table (
    id SERIAL PRIMARY KEY,
    my_table_id INT REFERENCES my_domain.my_table(id) ON DELETE CASCADE,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_md_my_table_column1 ON my_domain.my_table(column1);
CREATE INDEX idx_md_another_table_ref ON my_domain.another_table(my_table_id);

-- 確認
SELECT 'スキーマ作成完了: my_domain' as status;
```

**スキーマ作成実行:**

```bash
# PostgreSQLにスキーマ適用
docker-compose exec -T postgres psql -U postgres -d knowledge_ai_bot < \
  database/schema/domains/my_domain_schema.sql

# 確認
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot -c "\dt my_domain.*"
```

---

### Step 7: ドメイン有効化

**ファイル:** `config/app.config.yaml`

```yaml
app:
  active_domain: "my-domain"  # ← 変更
```

**再起動:**

```bash
docker-compose restart backend
```

---

## 設定ファイル詳細

### domain.yaml 完全リファレンス

```yaml
# ========================================
# ドメイン基本情報
# ========================================
domain:
  id: "my-domain"                    # 必須: ドメインID（kebab-case）
  name: "マイドメインボット"          # 必須: 表示名
  description: "ドメインの説明"       # 必須: 説明文
  version: "1.0.0"                   # 必須: バージョン
  author: "作成者名"                  # オプション

# ========================================
# エージェント設定
# ========================================
agent:
  name: "MyDomainAgent"              # 必須: エージェント名
  model: "gpt-4o"                    # オプション（デフォルト: gpt-4o）
  temperature: 0.7                   # オプション（デフォルト: 0.7）
  max_tokens: 4000                   # オプション（デフォルト: 4000）
  
  # プロンプトテンプレートキー（prompts.yamlから読み込む）
  prompt_templates:
    - "domain_instructions"          # 必須
    - "key_principles"               # オプション
    - "output_format"                # オプション

# ========================================
# ツール設定
# ========================================
tools:
  # 有効化するツール関数名のリスト
  enabled:
    - "tool_function_1"
    - "tool_function_2"

# ========================================
# データベース設定
# ========================================
database:
  # スキーマ名（省略時はドメインIDのsnake_case）
  schema: "my_domain"
  
  # スキーマ分離を使用するか（デフォルト: true）
  use_schema_separation: true
  
  # その他のDB設定（オプション）
  pool_size: 10
  timeout: 30

# ========================================
# UI設定
# ========================================
ui:
  # テーマカラー
  theme:
    primary: "#4A90E2"               # メインカラー
    secondary: "#50C878"             # サブカラー
    accent: "#FF6B6B"                # アクセントカラー
  
  # クイックアクション（サイドバー）
  quick_actions:
    - label: "アクション1"           # 表示ラベル
      query: "実際のクエリテキスト"  # 送信するクエリ
      icon: "🎯"                     # アイコン（絵文字）
    
    - label: "アクション2"
      query: "別のクエリ"
      icon: "📊"
  
  # サンプルクエリ（入力ボックス下）
  sample_queries:
    - "サンプルクエリ1"
    - "サンプルクエリ2"
    - "サンプルクエリ3"

# ========================================
# メトリクス（オプション）
# ========================================
metrics:
  custom_metrics:
    - name: "queries_processed"
      description: "処理したクエリ数"
      type: "counter"
    
    - name: "average_response_time"
      description: "平均応答時間"
      type: "gauge"
```

---

### prompts.yaml 完全リファレンス

```yaml
# ========================================
# ドメイン固有指示（必須）
# ========================================
domain_instructions: |
  あなたは[ドメイン名]の専門家です。
  
  ## 役割
  [役割の説明]
  
  ## 専門知識
  [専門知識の説明]
  
  ## タスク
  - [タスク1]
  - [タスク2]

# ========================================
# 重要な原則
# ========================================
key_principles: |
  ## 原則
  1. [原則1の説明]
  2. [原則2の説明]
  3. [原則3の説明]
  
  ## 制約
  - [制約1]
  - [制約2]

# ========================================
# 出力フォーマット
# ========================================
output_format: |
  ## 応答形式
  
  ### 1. [セクション1]
  [内容]
  
  ### 2. [セクション2]
  [内容]
  
  ### 3. [セクション3]
  [内容]

# ========================================
# 追加テンプレート（オプション）
# ========================================
analysis_procedure: |
  ## 分析手順
  1. [ステップ1]
  2. [ステップ2]
  3. [ステップ3]

tone_and_style: |
  ## トーン
  - [トーンの説明]
  
  ## スタイル
  - [スタイルの説明]

examples: |
  ## 良い例
  [例1]
  
  ## 悪い例
  [例2]
```

---

## ツール実装

### ツール関数のシグネチャ

```python
def tool_name(
    param1: str,              # 必須パラメータ
    param2: int = 10,         # オプションパラメータ（デフォルト値）
    param3: Optional[str] = None
) -> Union[List[Dict], Dict, str]:
    """
    ツールの説明（1行）
    
    詳細な説明（複数行可）
    
    Args:
        param1: パラメータ1の説明
        param2: パラメータ2の説明
        param3: パラメータ3の説明
    
    Returns:
        戻り値の説明
    
    Example:
        >>> tool_name("test", 5)
        {'result': 'success'}
    """
    pass
```

### データベース接続パターン

```python
def database_tool(query_param: str) -> List[Dict]:
    """データベースからデータ取得"""
    
    # スキーマ自動設定される接続取得
    conn = get_db_connection_for_domain()
    cursor = conn.cursor()
    
    try:
        # クエリ実行
        cursor.execute("""
            SELECT id, name, value
            FROM my_table
            WHERE name = %s
        """, (query_param,))
        
        # 結果を辞書リストに変換
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        return results
    
    except Exception as e:
        # エラーハンドリング
        print(f"Database error: {e}")
        return []
    
    finally:
        # 確実にクローズ
        cursor.close()
        conn.close()
```

### 外部API呼び出しパターン

```python
import requests

def api_tool(search_query: str) -> Dict[str, Any]:
    """外部APIからデータ取得"""
    
    try:
        response = requests.get(
            "https://api.example.com/search",
            params={"q": search_query},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "status": "success",
            "results": data.get("items", [])
        }
    
    except requests.RequestException as e:
        return {
            "status": "error",
            "message": str(e)
        }
```

---

## データベーススキーマ

### スキーマ作成のベストプラクティス

```sql
-- 1. スキーマ作成
CREATE SCHEMA IF NOT EXISTS my_domain;

-- 2. 検索パス設定（重要！）
SET search_path TO my_domain, public;

-- 3. テーブル作成（スキーマプレフィックス付き）
CREATE TABLE IF NOT EXISTS my_domain.my_table (
    -- テーブル定義
);

-- 4. インデックス作成（プレフィックスで重複回避）
CREATE INDEX idx_md_my_table_column ON my_domain.my_table(column);

-- 5. 外部キー（スキーマ指定）
ALTER TABLE my_domain.child_table
    ADD CONSTRAINT fk_parent
    FOREIGN KEY (parent_id) REFERENCES my_domain.parent_table(id);
```

### データ投入スクリプト例

```python
# scripts/import_my_domain_data.py
import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL', 
    'postgresql://postgres:password@localhost:5432/knowledge_ai_bot')
SCHEMA_NAME = 'my_domain'

def import_data():
    """データ投入"""
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # スキーマ設定
    cursor.execute(f"SET search_path TO {SCHEMA_NAME}, public")
    
    try:
        # データ投入
        cursor.execute("""
            INSERT INTO my_table (column1, column2)
            VALUES (%s, %s)
        """, ("value1", "value2"))
        
        conn.commit()
        print("✓ データ投入完了")
    
    except Exception as e:
        conn.rollback()
        print(f"エラー: {e}")
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import_data()
```

---

## テスト

### ドメイン動作確認チェックリスト

```bash
# 1. 設定ファイル確認
cat config/app.config.yaml | grep active_domain
# active_domain: "my-domain"

# 2. バックエンド起動ログ確認
docker-compose logs backend | grep "Domain"
# Domain 'マイドメインボット': Using schema 'my_domain'

# 3. ツールロード確認
docker-compose logs backend | grep "Loaded"
# Loaded 2 tools from app.domains.my_domain.tools

# 4. スキーマ確認
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot -c "\dt my_domain.*"

# 5. フロントエンド確認
curl http://localhost:8000/api/config/domain | jq '.domain.name'
# "マイドメインボット"

# 6. チャット動作確認
# http://localhost:3000 でクエリ送信
```

### ユニットテスト例

```python
# tests/test_my_domain_tools.py
import pytest
from app.domains.my_domain.tools import my_tool_function

def test_my_tool_function():
    """ツール関数のテスト"""
    result = my_tool_function("test", 5)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert 'key' in result[0]
```

---

## トラブルシューティング

### ツールがロードされない

**原因:** ツール関数名が `tools.enabled` リストにない

**解決:**
```yaml
# domain.yaml
tools:
  enabled:
    - "my_tool_function"  # ← 関数名と一致させる
```

### スキーマが見つからない

**原因:** スキーマが作成されていない

**解決:**
```bash
# スキーマ作成
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot -c \
  "CREATE SCHEMA IF NOT EXISTS my_domain;"

# または
docker-compose exec -T postgres psql -U postgres -d knowledge_ai_bot < \
  database/schema/domains/my_domain_schema.sql
```

### プロンプトが反映されない

**原因:** `prompt_templates` キーがprompts.yamlに存在しない

**解決:**
```yaml
# domain.yaml
agent:
  prompt_templates:
    - "domain_instructions"  # ← prompts.yamlに存在するキー

# prompts.yaml
domain_instructions: |
  プロンプト内容...
```

---

## まとめ

### 新ドメイン作成フロー

```
1. ディレクトリ作成
   ↓
2. domain.yaml作成
   ↓
3. prompts.yaml作成
   ↓
4. tools.py実装
   ↓
5. スキーマSQL作成
   ↓
6. スキーマ適用
   ↓
7. app.config.yaml更新
   ↓
8. 再起動
   ↓
9. テスト
```

### チェックリスト

- [ ] domain.yaml作成完了
- [ ] prompts.yaml作成完了
- [ ] tools.py実装完了
- [ ] スキーマSQL作成完了
- [ ] スキーマ適用完了
- [ ] app.config.yaml更新完了
- [ ] 再起動完了
- [ ] 動作確認完了

---

新ドメイン追加、お疲れ様でした！🎉