# システムアーキテクチャ

**バージョン**: 1.0.0  
**最終更新**: 2026年1月

---

## 📋 目次

1. [アーキテクチャ概要](#アーキテクチャ概要)
2. [3層設計](#3層設計)
3. [データフロー](#データフロー)
4. [コアフレームワーク](#コアフレームワーク)
5. [スキーマ分離](#スキーマ分離)
6. [設定駆動設計](#設定駆動設計)

---

## アーキテクチャ概要

### システム構成図

```
┌──────────────────────────────────────────────┐
│  ユーザー（ブラウザ）                          │
└──────────────┬───────────────────────────────┘
               │ HTTP/WebSocket
┌──────────────▼───────────────────────────────┐
│  Frontend (React + TypeScript)               │
│  ┌────────────────────────────────────────┐  │
│  │  汎用コンポーネント                     │  │
│  │  ├─ ChatInterface                      │  │
│  │  ├─ MessageList                        │  │
│  │  └─ InputBox                           │  │
│  └────────────────────────────────────────┘  │
└──────────────┬───────────────────────────────┘
               │ WS /ws/chat
┌──────────────▼───────────────────────────────┐
│  Backend (FastAPI)                           │
│  ┌────────────────────────────────────────┐  │
│  │  ConfigLoader                          │  │
│  │  ├─ app.config.yaml読み込み            │  │
│  │  ├─ agents.config.yaml読み込み         │  │
│  │  └─ domain.yaml読み込み                │  │
│  └────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────┐  │
│  │  AgentFactory                          │  │
│  │  ├─ プロンプト構築                      │  │
│  │  ├─ ツールロード                        │  │
│  │  └─ エージェント生成                    │  │
│  └────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────┐  │
│  │  Agent (OpenAI GPT-4o)                 │  │
│  │  └─ Function Calling                   │  │
│  └────────────┬───────────────────────────┘  │
└───────────────┼──────────────────────────────┘
                │
    ┌───────────┼───────────┐
    │           │           │
┌───▼───┐  ┌───▼────┐  ┌──▼─────┐
│ Tools │  │  DB    │  │ OpenAI │
│       │  │        │  │ API    │
└───┬───┘  └───┬────┘  └────────┘
    │          │
┌───▼──────────▼───┐
│  PostgreSQL      │
│  ├─ public       │  # 共通テーブル
│  ├─ horse_racing │  # 競馬ドメイン
│  └─ customer_    │  # サポートドメイン
│     support      │
└──────────────────┘
```

---

## 3層設計

### Layer 1: 設定層（YAML）

```yaml
# app.config.yaml - アプリケーション全体設定
app:
  active_domain: "horse-racing"  # ← ドメイン切替

# agents.config.yaml - エージェント基本設定
agents:
  default:
    base_instructions: |
      あなたは親切なAIアシスタントです...

# domains/horse-racing/domain.yaml - ドメイン設定
domain:
  id: "horse-racing"
  name: "競馬ナレッジボット"
  
agent:
  prompt_templates:
    - "domain_instructions"
    - "analysis_procedure"
  
tools:
  enabled:
    - "get_race_statistics"

database:
  schema: "horse_racing"
```

**特徴:**
- ✅ すべての動作をYAMLで制御
- ✅ コード変更不要
- ✅ バージョン管理可能

---

### Layer 2: コア層（汎用・再利用可能）

```python
# backend/app/core/config.py
class ConfigLoader:
    """設定ファイルローダー"""
    
    def load_yaml(self, filename: str) -> Dict
    def get_active_domain_config(self) -> Dict
    # ...

# backend/app/core/tool_loader.py
class ToolLoader:
    """ツール動的ロード"""
    
    def load_tools_for_domain(self, domain_id: str) -> List[Callable]
    # ...

# backend/app/core/agent_factory.py
class AgentFactory:
    """エージェント生成"""
    
    def create_agent(self) -> Agent
    def _build_instructions(self) -> str
    # ...
```

**特徴:**
- ✅ ドメイン非依存
- ✅ 完全に再利用可能
- ✅ テストしやすい

---

### Layer 3: ドメイン層（差し替え可能）

```python
# backend/app/domains/horse_racing/tools.py
def get_race_statistics(race_name: str, category: str) -> List[Dict]:
    """競馬レース統計取得"""
    # 競馬固有のロジック
    pass

# backend/app/domains/customer_support/tools.py
def search_knowledge_base(query: str) -> List[Dict]:
    """ナレッジベース検索"""
    # サポート固有のロジック
    pass
```

**特徴:**
- ✅ ドメイン固有実装
- ✅ 独立して開発可能
- ✅ 簡単に差し替え

---

## データフロー

### ユーザークエリ処理フロー

```
1. ユーザー入力
   "シンザン記念の傾向を教えて"
   ↓
2. WebSocket → Backend
   ↓
3. ConfigLoader
   ├─ active_domain取得 → "horse-racing"
   ├─ domain.yaml読み込み
   └─ prompts.yaml読み込み
   ↓
4. AgentFactory
   ├─ プロンプト構築
   │   ├─ base_instructions
   │   └─ domain_instructions
   ├─ ツールロード
   │   └─ get_race_statistics
   └─ エージェント生成
   ↓
5. Agent (GPT-4o)
   ├─ クエリ解析
   ├─ Function Calling判定
   │   └─ get_race_statistics("シンザン記念", "popularity")
   └─ ツール実行
   ↓
6. Tool実行
   ├─ db_utils.get_db_connection_for_domain()
   │   └─ SET search_path TO horse_racing
   ├─ SELECT * FROM races WHERE race_name = 'シンザン記念'
   └─ データ取得
   ↓
7. Agent応答生成
   ├─ 統計データ分析
   ├─ Markdown生成
   └─ ストリーミング送信
   ↓
8. Frontend表示
   └─ react-markdownで描画
```

---

## コアフレームワーク

### ConfigLoader（設定管理）

**責務:**
- YAMLファイル読み込み
- 環境変数展開
- 設定内参照解決

**実装例:**

```python
class ConfigLoader:
    def __init__(self, config_dir: str = "/app/config"):
        self.config_dir = Path(config_dir)
        self._cache: Dict[str, Any] = {}
    
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """YAMLファイル読み込み"""
        if filename in self._cache:
            return self._cache[filename]
        
        filepath = self.config_dir / filename
        with open(filepath, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 環境変数展開 ${VAR_NAME}
        config = self._expand_env_vars(config)
        
        # 相互参照解決 ${llm.model}
        config = self._resolve_references(config, config)
        
        self._cache[filename] = config
        return config
    
    def get_active_domain_config(self) -> Dict[str, Any]:
        """アクティブドメイン設定取得"""
        app_config = self.load_yaml("app.config.yaml")
        active_domain = app_config['app']['active_domain']
        return self.load_yaml(f"domains/{active_domain}/domain.yaml")
```

**使用例:**

```python
config_loader = ConfigLoader()
domain_config = config_loader.get_active_domain_config()
# → domains/horse-racing/domain.yaml の内容
```

---

### ToolLoader（ツール動的ロード）

**責務:**
- ドメイン固有ツールの動的インポート
- ツール関数の検出
- ツールリスト生成

**実装例:**

```python
class ToolLoader:
    def load_tools_for_domain(self, domain_id: str) -> List[Callable]:
        """ドメインのツールをロード"""
        module_name = f"app.domains.{domain_id.replace('-', '_')}.tools"
        
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            return []
        
        tools = []
        for name in dir(module):
            obj = getattr(module, name)
            if callable(obj) and not name.startswith('_'):
                tools.append(obj)
        
        return tools
```

**使用例:**

```python
tool_loader = ToolLoader()
tools = tool_loader.load_tools_for_domain("horse-racing")
# → [get_race_statistics, analyze_elimination_conditions]
```

---

### AgentFactory（エージェント生成）

**責務:**
- プロンプト構築
- ツール統合
- エージェントインスタンス生成

**実装例:**

```python
class AgentFactory:
    def create_agent(self) -> Agent:
        """エージェント生成"""
        # 1. 設定読み込み
        domain_config = config_loader.get_active_domain_config()
        
        # 2. プロンプト構築
        instructions = self._build_instructions()
        
        # 3. ツールロード
        tools = tool_loader.load_tools_for_domain(
            domain_config['domain']['id']
        )
        
        # 4. エージェント生成
        agent = Agent(
            name=domain_config['agent']['name'],
            model="gpt-4o",
            instructions=instructions,
            tools=tools
        )
        
        return agent
    
    def _build_instructions(self) -> str:
        """プロンプト構築"""
        # base_instructions + domain_instructions
        pass
```

---

## スキーマ分離

### データベース構造

```
knowledge_ai_bot (Database)
│
├── public (Schema)              # 共通テーブル
│   ├── users                    # ユーザー
│   ├── conversations            # 会話履歴
│   └── sessions                 # セッション
│
├── horse_racing (Schema)        # 競馬ドメイン
│   ├── races                    # レース情報
│   ├── race_results             # レース結果
│   ├── race_statistics          # 統計データ
│   └── elimination_statistics   # 消去法統計
│
└── customer_support (Schema)    # サポートドメイン
    ├── tickets                  # チケット
    ├── knowledge_base           # ナレッジベース
    └── orders                   # 注文情報
```

### スキーマ切替の仕組み

```python
# db_utils.py
def get_db_connection_for_domain():
    """ドメインのDB接続取得"""
    domain_config = config_loader.get_active_domain_config()
    
    # スキーマ名取得
    schema = domain_config.get('database', {}).get('schema', 'public')
    
    # 接続
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # スキーマ設定（重要！）
    cursor.execute(f"SET search_path TO {schema}, public")
    
    return conn
```

**検索パス設定後:**

```sql
-- この後のクエリは自動的に horse_racing スキーマを参照
SELECT * FROM races WHERE race_name = 'シンザン記念';
-- ↓ 実際には
SELECT * FROM horse_racing.races WHERE race_name = 'シンザン記念';
```

### メリット

✅ **データ完全分離**
- ドメイン間でテーブル名が衝突しない
- 誤って他ドメインのデータにアクセスしない

✅ **管理が容易**
- 1つのデータベースで管理
- バックアップが簡単
- 接続管理がシンプル

✅ **柔軟性**
- 新ドメイン追加が簡単（CREATE SCHEMA）
- ドメイン削除も簡単（DROP SCHEMA CASCADE）

---

## 設定駆動設計

### ドメイン切替の流れ

```
┌─────────────────────────────────┐
│  app.config.yaml                │
│  active_domain: "horse-racing"  │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  ConfigLoader                   │
│  get_active_domain_config()     │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  domains/horse-racing/          │
│  ├─ domain.yaml                 │
│  └─ prompts.yaml                │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  AgentFactory                   │
│  ├─ プロンプト構築               │
│  └─ ツールロード                 │
└────────────┬────────────────────┘
             │
             ▼
┌─────────────────────────────────┐
│  Agent実行                       │
└─────────────────────────────────┘
```

### 環境変数展開

```yaml
# config/app.config.yaml
llm:
  api_key: "${OPENAI_API_KEY}"  # 環境変数から展開
  endpoint: "${OPENAI_ENDPOINT}"
```

```python
# 展開処理
def _expand_env_vars(self, obj: Any) -> Any:
    if isinstance(obj, str):
        pattern = r'\$\{([^}]+)\}'
        matches = re.findall(pattern, obj)
        for match in matches:
            env_value = os.getenv(match, match)
            obj = obj.replace(f'${{{match}}}', env_value)
    return obj
```

### 設定内参照

```yaml
# agents.config.yaml
agents:
  default:
    model: "gpt-4o"

# domains/horse-racing/domain.yaml
agent:
  model: "${agents.default.model}"  # 参照
```

---

## パフォーマンス最適化

### キャッシング戦略

```python
# ConfigLoaderでYAMLキャッシュ
class ConfigLoader:
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    def load_yaml(self, filename: str):
        if filename in self._cache:
            return self._cache[filename]  # キャッシュヒット
        # ... ファイル読み込み ...
        self._cache[filename] = config
        return config
```

### 接続プーリング

```python
# PostgreSQL接続プール
from psycopg2.pool import SimpleConnectionPool

pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    dsn=DATABASE_URL
)

def get_db_connection():
    return pool.getconn()
```

---

## セキュリティ

### 環境変数管理

```bash
# .env（Gitにコミットしない）
OPENAI_API_KEY=sk-proj-xxx
DATABASE_URL=postgresql://...
```

```bash
# .gitignore
.env
.env.local
.env.*.local
```

### SQLインジェクション対策

```python
# ❌ NG: 文字列結合
cursor.execute(f"SELECT * FROM races WHERE race_name = '{race_name}'")

# ✅ OK: プレースホルダー
cursor.execute("SELECT * FROM races WHERE race_name = %s", (race_name,))
```

### スキーマ分離によるデータ保護

```python
# horse_racing スキーマに設定
cursor.execute("SET search_path TO horse_racing, public")

# customer_support のデータには自動的にアクセスできない
cursor.execute("SELECT * FROM tickets")  # エラー
```

---

## まとめ

### アーキテクチャの特徴

✅ **3層設計** - 設定 / コア / ドメイン  
✅ **スキーマ分離** - ドメインごとにデータ完全分離  
✅ **設定駆動** - YAMLで全動作制御  
✅ **動的ロード** - ツール・エージェントを動的生成  
✅ **拡張性** - 新ドメイン追加が容易  

### ベストプラクティス

1. **設定とコードを分離**
2. **汎用部分とドメイン固有部分を明確に区別**
3. **データベーススキーマでドメイン分離**
4. **環境変数で機密情報管理**
5. **キャッシュで性能最適化**

---

このアーキテクチャにより、**保守性・拡張性・再利用性**の高いシステムが実現できています。