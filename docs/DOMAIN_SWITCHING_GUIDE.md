# ドメイン切替ガイド

このガイドでは、複数のドメイン間でチャットボットを切り替える方法を説明します。

---

## 🎯 概要

このテンプレートは、設定ファイルを変更するだけで、全く異なるドメインのチャットボットに切り替えることができます。

**利用可能なドメイン:**
- `horse-racing`: 競馬ナレッジボット
- `customer-support`: カスタマーサポートボット
- （あなたのカスタムドメイン）

---

## 🔄 ドメイン切替手順

### **Step 1: 設定ファイル編集**

`config/app.config.yaml` を開いて、`active_domain` を変更します。

```yaml
# config/app.config.yaml
app:
  name: "Keiba-Knowledge AI"
  version: "0.1.0"
  environment: "development"
  
  # 現在のドメイン（ここを変更）
  active_domain: "customer-support"  # ← "horse-racing" から変更
```

### **Step 2: Dockerコンテナ再起動**

```bash
# プロジェクトルートで実行
docker-compose restart backend

# ログ確認
docker-compose logs -f backend
```

### **Step 3: 動作確認**

ブラウザで http://localhost:3000 にアクセス。

**期待される変化:**
- ✅ アプリ名が変わる（競馬ナレッジボット → カスタマーサポートボット）
- ✅ クイックアクションが変わる
- ✅ サンプルクエリが変わる
- ✅ テーマカラーが変わる
- ✅ エージェントの応答スタイルが変わる

---

## 🧪 テスト例

### **horse-racing ドメイン**

```yaml
active_domain: "horse-racing"
```

**テストクエリ:**
```
シンザン記念の傾向を教えて
```

**期待される動作:**
- ツール呼び出し: `get_race_statistics`
- 統計データの表示（人気別・枠順別）
- Markdownテーブル表示

---

### **customer-support ドメイン**

```yaml
active_domain: "customer-support"
```

**テストクエリ:**
```
注文番号12345の配送状況を確認したい
```

**期待される動作:**
- ツール呼び出し: `check_order_status`
- 配送状況の表示
- 丁寧な敬語での応答

---

## 📊 ドメイン間の違い

| 項目 | horse-racing | customer-support |
|------|--------------|------------------|
| **エージェント名** | RaceTrendAnalyzer | SupportAssistant |
| **トーン** | 客観的・データ重視 | 親切・丁寧 |
| **ツール** | レース統計、消去法分析 | ナレッジ検索、チケット作成 |
| **テーマカラー** | 青系 | 青・緑系 |
| **出力スタイル** | 統計表・グラフ中心 | 箇条書き・手順中心 |

---

## 🛠️ トラブルシューティング

### **エラー1: ドメイン設定が見つからない**

```
FileNotFoundError: Domain config not found: customer-support
```

**解決方法:**
```bash
# ドメイン設定が存在するか確認
ls config/domains/customer-support/domain.yaml

# なければ作成
python scripts/create_domain.py customer-support "カスタマーサポートボット"
```

### **エラー2: ツールモジュールが見つからない**

```
ModuleNotFoundError: No module named 'app.domains.customer_support'
```

**解決方法:**
```bash
# ディレクトリとファイルを確認
ls backend/app/domains/customer_support/__init__.py
ls backend/app/domains/customer_support/tools.py

# なければ作成
mkdir -p backend/app/domains/customer_support
touch backend/app/domains/customer_support/__init__.py
# tools.py を作成
```

### **エラー3: プロンプトが反映されない**

**解決方法:**
```bash
# キャッシュクリア
docker-compose down
docker-compose up -d

# または完全再ビルド
docker-compose build backend
docker-compose up -d
```

---

## 🎓 学習ポイント

### **設定駆動設計の利点**

1. **コード変更不要**
   - YAMLファイルの編集だけでドメイン切替
   - Python コードは一切変更しない

2. **保守性向上**
   - ドメインごとに独立した設定
   - 変更の影響範囲が明確

3. **拡張性**
   - 新しいドメインの追加が容易
   - 既存ドメインに影響なし

4. **テンプレート化**
   - 他プロジェクトへの転用が簡単
   - ベストプラクティスの共有

---

## 📚 次のステップ

1. **新ドメイン作成**
   ```bash
   python scripts/create_domain.py my-domain "マイドメイン"
   ```

2. **プロンプトカスタマイズ**
   ```bash
   vim config/domains/my-domain/prompts.yaml
   ```

3. **ツール実装**
   ```bash
   vim backend/app/domains/my_domain/tools.py
   ```

4. **UI設定**
   ```bash
   vim config/domains/my-domain/domain.yaml
   ```

5. **ドメイン切替**
   ```bash
   # config/app.config.yaml
   active_domain: "my-domain"
   
   # 再起動
   docker-compose restart backend
   ```

---

**ドメイン切替を楽しんでください！** 🚀