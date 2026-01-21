#!/usr/bin/env python3
"""
新ドメイン作成スクリプト

使用方法:
    python scripts/create_domain.py my-domain "マイドメイン"

例:
    python scripts/create_domain.py e-commerce "ECサイトボット"
"""
import os
import sys
from pathlib import Path
import yaml


def create_domain(domain_id: str, domain_name: str):
    """
    新ドメイン作成
    
    Args:
        domain_id: ドメインID（例: "my-domain"）
        domain_name: ドメイン表示名（例: "マイドメイン"）
    """
    
    # プロジェクトルート検出
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"Creating domain: {domain_id} ({domain_name})")
    print(f"Project root: {project_root}")
    
    # ========================================
    # 1. 設定ファイルディレクトリ作成
    # ========================================
    config_dir = project_root / "config" / "domains" / domain_id
    config_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created: {config_dir}")
    
    # ========================================
    # 2. domain.yaml作成
    # ========================================
    domain_config = {
        'domain': {
            'id': domain_id,
            'name': domain_name,
            'description': f'{domain_name}のチャットボット',
            'version': '1.0.0',
            'author': 'Masato'
        },
        'agent': {
            'name': f'{domain_id.replace("-", "_").title()}Agent',
            'model': 'gpt-4o',
            'temperature': 0.7,
            'max_tokens': 4000,
            'prompt_templates': [
                'domain_instructions',
                'guidelines',
                'output_format'
            ]
        },
        'tools': {
            'enabled': []
        },
        'ui': {
            'theme': {
                'primary': '#4A90E2',
                'secondary': '#50C878',
                'accent': '#FF6B6B'
            },
            'quick_actions': [],
            'sample_queries': []
        }
    }
    
    domain_yaml_path = config_dir / "domain.yaml"
    with open(domain_yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(domain_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"✓ Created: {domain_yaml_path}")
    
    # ========================================
    # 3. prompts.yaml作成
    # ========================================
    prompts_config = {
        'domain_instructions': f'あなたは{domain_name}の専門家です。\n\n## 基本方針\n- 正確な情報提供\n- 分かりやすい説明\n- 親切な対応\n',
        'guidelines': '## ガイドライン\n\n### 応答スタイル\n- 簡潔で明確な表現\n- 専門用語には説明を添える\n- 例を使って分かりやすく\n',
        'output_format': '## 出力形式\n\n### 標準応答\n1. 質問内容の確認\n2. 回答\n3. 補足情報（必要に応じて）\n'
    }
    
    prompts_yaml_path = config_dir / "prompts.yaml"
    with open(prompts_yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(prompts_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    
    print(f"✓ Created: {prompts_yaml_path}")
    
    # ========================================
    # 4. バックエンドドメインディレクトリ作成
    # ========================================
    domain_snake = domain_id.replace('-', '_')
    domain_backend_dir = project_root / 'backend' / 'app' / 'domains' / domain_snake
    domain_backend_dir.mkdir(parents=True, exist_ok=True)
    
    # __init__.py
    init_file = domain_backend_dir / '__init__.py'
    init_file.write_text(f'"""\n{domain_name}ドメイン実装\n"""\n', encoding='utf-8')
    print(f"✓ Created: {init_file}")
    
    # tools.py（スタブ）
    tools_file = domain_backend_dir / 'tools.py'
    tools_template = f'''"""
{domain_name}ツール

このファイルは app/domains/{domain_snake}/tools.py に配置されます。
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def example_tool(query: str) -> Dict[str, Any]:
    """
    サンプルツール
    
    Args:
        query: クエリ
    
    Returns:
        結果
    """
    logger.info(f"example_tool called: query={{query}}")
    
    return {{
        "result": f"処理しました: {{query}}"
    }}


# ========================================
# ToolLoader用の関数
# ========================================

def get_tools() -> List[Dict[str, Any]]:
    """
    OpenAI Function Calling用のツール定義を返す
    
    Returns:
        ツール定義リスト
    """
    return [
        {{
            "type": "function",
            "function": {{
                "name": "example_tool",
                "description": "サンプルツール",
                "parameters": {{
                    "type": "object",
                    "properties": {{
                        "query": {{
                            "type": "string",
                            "description": "クエリ"
                        }}
                    }},
                    "required": ["query"]
                }}
            }}
        }}
    ]


def get_tool_functions() -> Dict[str, Any]:
    """
    実行可能な関数マップを返す
    
    Returns:
        関数マップ {{'function_name': function}}
    """
    return {{
        "example_tool": example_tool
    }}
'''
    
    tools_file.write_text(tools_template, encoding='utf-8')
    print(f"✓ Created: {tools_file}")
    
    # ========================================
    # 完了メッセージ
    # ========================================
    print(f"""
✅ ドメイン '{domain_name}' を作成しました！

次のステップ:
1. プロンプト編集:
   config/domains/{domain_id}/prompts.yaml

2. ツール実装:
   backend/app/domains/{domain_snake}/tools.py

3. UI設定:
   config/domains/{domain_id}/domain.yaml

4. ドメイン有効化:
   config/app.config.yaml の active_domain を '{domain_id}' に変更

5. 再起動:
   docker-compose restart backend
""")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python scripts/create_domain.py <domain_id> <domain_name>")
        print("Example: python scripts/create_domain.py e-commerce 'ECサイトボット'")
        sys.exit(1)
    
    domain_id = sys.argv[1]
    domain_name = sys.argv[2]
    
    # バリデーション
    if not domain_id.replace('-', '').replace('_', '').isalnum():
        print("Error: domain_id は英数字とハイフン、アンダースコアのみ使用できます")
        sys.exit(1)
    
    create_domain(domain_id, domain_name)