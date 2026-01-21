# データベース設計ガイド

**バージョン**: 1.0.0  
**最終更新**: 2026年1月

---

## 📋 目次

1. [スキーマ分離アーキテクチャ](#スキーマ分離アーキテクチャ)
2. [データベース構造](#データベース構造)
3. [スキーマ作成](#スキーマ作成)
4. [データ投入](#データ投入)
5. [マイグレーション](#マイグレーション)
6. [ベストプラクティス](#ベストプラクティス)

---

## スキーマ分離アーキテクチャ

### 概要

このテンプレートでは、**PostgreSQLスキーマ分離**によってドメインごとにデータを完全に分離しています。

### メリット

✅ **データ完全分離**
- ドメイン間でテーブル名が衝突しない
- 誤って他ドメインのデータにアクセスしない

✅ **管理が容易**
- 1つのデータベースで管理
- バックアップが簡単
- 接続管理がシンプル

✅ **柔軟性**
- 新ドメイン追加: `CREATE SCHEMA`
- ドメイン削除: `DROP SCHEMA CASCADE`
- スキーマ単位でダンプ・リストア可能

---

## データベース構造

### 全体構成

```
knowledge_ai_bot (Database)
│
├── public (Schema)              # 共通テーブル
│   ├── users                    # ユーザー情報
│   ├── conversations            # 会話履歴
│   ├── sessions                 # セッション管理
│   └── domain_access            # ドメインアクセス権
│
├── horse_racing (Schema)        # 競馬ドメイン
│   ├── races                    # レース情報
│   ├── race_results             # レース結果
│   ├── race_statistics          # 統計データ
│   └── elimination_statistics   # 消去法統計
│
├── customer_support (Schema)    # サポートドメイン
│   ├── tickets                  # チケット
│   ├── knowledge_base           # ナレッジベース
│   ├── orders                   # 注文情報
│   └── faqs                     # FAQ
│
└── [your_domain] (Schema)       # 新規ドメイン
    └── [tables...]
```

### スキーマ命名規則

| ドメインID | スキーマ名 | 説明 |
|-----------|-----------|------|
| `horse-racing` | `horse_racing` | kebab-case → snake_case |
| `customer-support` | `customer_support` | kebab-case → snake_case |
| `e-commerce` | `e_commerce` | kebab-case → snake_case |

**ルール:** ドメインIDのハイフンをアンダースコアに変換

---

## スキーマ作成

### 基本テンプレート

```sql
-- ========================================
-- [ドメイン名] スキーマ
-- ========================================

-- 1. スキーマ作成
CREATE SCHEMA IF NOT EXISTS [schema_name];

-- 2. 検索パス設定（このセッション用）
SET search_path TO [schema_name], public;

-- 3. テーブル作成
CREATE TABLE IF NOT EXISTS [schema_name].[table_name] (
    id SERIAL PRIMARY KEY,
    column1 VARCHAR(200) NOT NULL,
    column2 TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. インデックス作成
CREATE INDEX idx_[prefix]_[table]_[column] 
    ON [schema_name].[table_name]([column]);

-- 5. 外部キー制約
ALTER TABLE [schema_name].[child_table]
    ADD CONSTRAINT fk_[name]
    FOREIGN KEY ([column]) 
    REFERENCES [schema_name].[parent_table](id)
    ON DELETE CASCADE;

-- 6. 確認
SELECT 'スキーマ作成完了: [schema_name]' as status;
```

### 実例: 競馬ドメイン

```sql
-- horse_racing スキーマ
CREATE SCHEMA IF NOT EXISTS horse_racing;
SET search_path TO horse_racing, public;

-- レース情報テーブル
CREATE TABLE IF NOT EXISTS horse_racing.races (
    race_id SERIAL PRIMARY KEY,
    race_name VARCHAR(200) NOT NULL,
    race_date DATE NOT NULL,
    track_name VARCHAR(50),
    distance INT,
    surface VARCHAR(20),
    grade VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- レース結果テーブル
CREATE TABLE IF NOT EXISTS horse_racing.race_results (
    result_id SERIAL PRIMARY KEY,
    race_id INT REFERENCES horse_racing.races(race_id) ON DELETE CASCADE,
    finish_position INT NOT NULL,
    horse_name VARCHAR(100) NOT NULL,
    popularity INT,
    jockey_name VARCHAR(100),
    last_3f_time DECIMAL(4,1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- インデックス
CREATE INDEX idx_hr_races_name ON horse_racing.races(race_name);
CREATE INDEX idx_hr_results_race ON horse_racing.race_results(race_id);
```

### スキーマ適用

```bash
# SQLファイル実行
docker-compose exec -T postgres psql -U postgres -d knowledge_ai_bot < \
  database/schema/domains/horse_racing_schema.sql

# 確認
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot -c "\dn"
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot -c "\dt horse_racing.*"
```

---

## データ投入

### パターン1: SQL直接投入

```sql
-- SET search_path でスキーマ指定
SET search_path TO horse_racing, public;

-- 以降のクエリは horse_racing スキーマを参照
INSERT INTO races (race_name, race_date, track_name)
VALUES ('シンザン記念', '2025-01-06', '中京');

-- または明示的にスキーマ指定
INSERT INTO horse_racing.races (race_name, race_date, track_name)
VALUES ('シンザン記念', '2025-01-06', '中京');
```

### パターン2: Python スクリプト

```python
#!/usr/bin/env python3
"""
データ投入スクリプト
"""
import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL', 
    'postgresql://postgres:password@localhost:5432/knowledge_ai_bot')
SCHEMA_NAME = 'horse_racing'

def import_data():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # スキーマ設定（重要！）
    cursor.execute(f"SET search_path TO {SCHEMA_NAME}, public")
    print(f"使用スキーマ: {SCHEMA_NAME}")
    
    try:
        # データ投入
        cursor.execute("""
            INSERT INTO races (race_name, race_date, track_name)
            VALUES (%s, %s, %s)
            RETURNING race_id
        """, ('シンザン記念', '2025-01-06', '中京'))
        
        race_id = cursor.fetchone()[0]
        print(f"レース追加: race_id={race_id}")
        
        conn.commit()
        print("✓ データ投入完了")
    
    except Exception as e:
        conn.rollback()
        print(f"エラー: {e}")
        raise
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    import_data()
```

### パターン3: CSVインポート

```bash
# CSVファイル準備
cat > /tmp/races.csv << 'EOF'
race_name,race_date,track_name
シンザン記念,2025-01-06,中京
有馬記念,2024-12-22,中山
EOF

# PostgreSQL COPY コマンド
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot << 'EOF'
SET search_path TO horse_racing, public;

COPY races (race_name, race_date, track_name)
FROM '/tmp/races.csv'
DELIMITER ','
CSV HEADER;
EOF
```

---

## マイグレーション

### ゼロからセットアップ

```bash
# 1. データベース作成
docker-compose exec postgres psql -U postgres << 'EOF'
CREATE DATABASE knowledge_ai_bot;
EOF

# 2. スキーマ作成
docker-compose exec -T postgres psql -U postgres -d knowledge_ai_bot < \
  database/schema/domains/horse_racing_schema.sql

# 3. データ投入
docker-compose exec backend python scripts/parse_keibalab_text.py \
  --input scripts/data/shinzan_kinen.txt \
  --race-name 'シンザン記念' \
  --grade 'G3'

# 4. 確認
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot << 'EOF'
SET search_path TO horse_racing, public;
SELECT COUNT(*) FROM races;
SELECT COUNT(*) FROM race_results;
EOF
```

### 既存データベースからの移行

```bash
# 1. 既存DBからエクスポート
docker-compose exec postgres pg_dump -U postgres -d old_database \
  -t races -t race_results \
  --data-only --column-inserts > /tmp/data_export.sql

# 2. スキーマ名を置換
sed -i 's/public\./horse_racing\./g' /tmp/data_export.sql
sed -i '1i SET search_path TO horse_racing, public;' /tmp/data_export.sql

# 3. 新DBにインポート
docker-compose exec -T postgres psql -U postgres -d knowledge_ai_bot < /tmp/data_export.sql

# 4. 確認
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot -c \
  "SET search_path TO horse_racing; SELECT COUNT(*) FROM races;"
```

### スキーマ間データコピー

```sql
-- public スキーマから horse_racing スキーマへコピー
INSERT INTO horse_racing.races
SELECT * FROM public.races;

-- または
CREATE TABLE horse_racing.races AS
SELECT * FROM public.races;
```

---

## ベストプラクティス

### 1. スキーマ命名

✅ **推奨:**
```
horse_racing
customer_support
e_commerce
```

❌ **非推奨:**
```
HorseRacing    # スネークケースで統一
horse-racing   # ハイフン不可
hr             # 省略形は避ける
```

### 2. テーブル命名

✅ **推奨:**
```sql
-- スキーマプレフィックス付き
CREATE TABLE horse_racing.races (...);
CREATE TABLE horse_racing.race_results (...);
```

❌ **非推奨:**
```sql
-- スキーマプレフィックスなし（曖昧）
CREATE TABLE races (...);
```

### 3. インデックス命名

```sql
-- パターン: idx_[schema_prefix]_[table]_[column]
CREATE INDEX idx_hr_races_name ON horse_racing.races(race_name);
CREATE INDEX idx_hr_results_finish ON horse_racing.race_results(finish_position);

-- 複合インデックス
CREATE INDEX idx_hr_races_name_date ON horse_racing.races(race_name, race_date);
```

**プレフィックス例:**
- `horse_racing` → `hr`
- `customer_support` → `cs`
- `e_commerce` → `ec`

### 4. 外部キー制約

```sql
-- スキーマ明示
ALTER TABLE horse_racing.race_results
    ADD CONSTRAINT fk_race
    FOREIGN KEY (race_id)
    REFERENCES horse_racing.races(race_id)
    ON DELETE CASCADE;
```

### 5. search_path 設定

```python
# Python: 接続時に設定
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()
cursor.execute("SET search_path TO horse_racing, public")
```

```sql
-- SQL: セッション開始時に設定
SET search_path TO horse_racing, public;
```

**フォールバック:**
- `horse_racing` スキーマに存在しないテーブルは `public` から検索
- 例: `users`, `conversations` は `public` に存在

### 6. バックアップ・リストア

```bash
# スキーマ単位でバックアップ
docker-compose exec postgres pg_dump -U postgres -d knowledge_ai_bot \
  --schema=horse_racing \
  -F c -f /tmp/horse_racing_backup.dump

# リストア
docker-compose exec postgres pg_restore -U postgres -d knowledge_ai_bot \
  --schema=horse_racing \
  /tmp/horse_racing_backup.dump
```

### 7. データ整合性

```sql
-- UNIQUE制約（スキーマ内で一意）
ALTER TABLE horse_racing.race_statistics
    ADD CONSTRAINT uniq_hr_race_category
    UNIQUE (race_name, category, condition);

-- CHECK制約
ALTER TABLE horse_racing.races
    ADD CONSTRAINT check_distance
    CHECK (distance > 0 AND distance <= 4000);
```

---

## トラブルシューティング

### エラー: relation does not exist

**原因:** スキーマが設定されていない

```python
# ❌ NG
cursor.execute("SELECT * FROM races")  # public.races を探す

# ✅ OK
cursor.execute("SET search_path TO horse_racing, public")
cursor.execute("SELECT * FROM races")  # horse_racing.races を探す
```

### エラー: schema does not exist

**原因:** スキーマが作成されていない

```bash
# スキーマ作成
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot -c \
  "CREATE SCHEMA IF NOT EXISTS horse_racing;"
```

### スキーマ確認コマンド

```bash
# すべてのスキーマ一覧
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot -c "\dn"

# 特定スキーマのテーブル一覧
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot -c "\dt horse_racing.*"

# テーブル詳細
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot -c "\d horse_racing.races"

# データ確認
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot << 'EOF'
SET search_path TO horse_racing, public;
SELECT COUNT(*) FROM races;
EOF
```

---

## スキーマ管理ツール

### スキーマ一覧表示

```python
# scripts/list_schemas.py
import psycopg2
import os

DATABASE_URL = os.getenv('DATABASE_URL')

def list_schemas():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
        ORDER BY schema_name
    """)
    
    print("=== スキーマ一覧 ===")
    for row in cursor.fetchall():
        schema_name = row[0]
        
        # テーブル数取得
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = %s
        """, (schema_name,))
        
        table_count = cursor.fetchone()[0]
        print(f"  {schema_name}: {table_count} tables")
    
    conn.close()

if __name__ == "__main__":
    list_schemas()
```

### スキーマ削除

```bash
# ⚠️ 注意: すべてのテーブルとデータが削除されます
docker-compose exec postgres psql -U postgres -d knowledge_ai_bot -c \
  "DROP SCHEMA IF EXISTS horse_racing CASCADE;"
```

---

## まとめ

### スキーマ分離の利点

✅ **データ分離**: ドメイン間で完全分離  
✅ **柔軟性**: スキーマ単位で管理  
✅ **拡張性**: 新ドメイン追加が容易  
✅ **保守性**: スキーマ単位でバックアップ・リストア  

### 重要ポイント

1. **スキーマ名はsnake_case**
2. **search_path を必ず設定**
3. **テーブル作成時にスキーマプレフィックス**
4. **インデックス名にプレフィックス**
5. **外部キーもスキーマ指定**

---

これでスキーマ分離を活用した柔軟なデータベース設計が可能です！