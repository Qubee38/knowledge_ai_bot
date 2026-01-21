"""
設定管理モジュール（拡張版）
YAML設定ファイルを読み込み、環境変数と統合
プロンプトテンプレート管理機能を追加
"""
import os
import yaml
import re
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic_settings import BaseSettings

class AppSettings(BaseSettings):
    """環境変数設定"""
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:password@postgres:5432/keiba_knowledge"
    REDIS_URL: str = "redis://redis:6379/0"
    
    CONFIG_DIR: str = "/app/config"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class ConfigLoader:
    """設定ファイルローダー（拡張版）"""
    
    def __init__(self, config_dir: str = None):
        self.config_dir = Path(config_dir or os.getenv("CONFIG_DIR", "/app/config"))
        self._cache: Dict[str, Any] = {}
    
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """YAMLファイル読み込み"""
        if filename in self._cache:
            return self._cache[filename]
        
        filepath = self.config_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 環境変数展開
        config = self._expand_env_vars(config)
        
        # 相互参照解決（${llm.model}等）
        config = self._resolve_references(config, config)
        
        self._cache[filename] = config
        return config
    
    def _expand_env_vars(self, obj: Any) -> Any:
        """環境変数を展開 ${VAR_NAME}"""
        if isinstance(obj, dict):
            return {k: self._expand_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._expand_env_vars(item) for item in obj]
        elif isinstance(obj, str):
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, obj)
            for match in matches:
                env_value = os.getenv(match, match)
                obj = obj.replace(f'${{{match}}}', env_value)
            return obj
        else:
            return obj
    
    def _resolve_references(self, obj: Any, root: Dict) -> Any:
        """設定内参照を解決 ${llm.model}"""
        if isinstance(obj, dict):
            return {k: self._resolve_references(v, root) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_references(item, root) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            # ${section.key}形式
            path = obj[2:-1].split('.')
            value = root
            for key in path:
                value = value.get(key, obj)
                if value == obj:
                    break
            return value
        else:
            return obj
    
    def load_app_config(self) -> Dict[str, Any]:
        """アプリケーション設定"""
        return self.load_yaml("app.config.yaml")
    
    def load_agent_config(self) -> Dict[str, Any]:
        """エージェント設定"""
        try:
            return self.load_yaml("agents.config.yaml")
        except FileNotFoundError:
            # フォールバック: 空の設定を返す
            return {
                "agents": {
                    "default": {
                        "name": "AssistantAgent",
                        "base_instructions": "あなたは親切なAIアシスタントです。"
                    }
                }
            }
    
    def load_domain_config(self, domain_id: str) -> Dict[str, Any]:
        """
        ドメイン設定読み込み
        
        新形式: domains/{domain_id}/domain.yaml
        旧形式: domains/{domain_id}.yaml（後方互換）
        """
        # 新形式を試す
        new_format_path = self.config_dir / "domains" / domain_id / "domain.yaml"
        if new_format_path.exists():
            return self.load_yaml(f"domains/{domain_id}/domain.yaml")
        
        # 旧形式にフォールバック
        old_format_path = self.config_dir / "domains" / f"{domain_id}.yaml"
        if old_format_path.exists():
            return self.load_yaml(f"domains/{domain_id}.yaml")
        
        raise FileNotFoundError(f"Domain config not found: {domain_id}")
    
    def load_domain_prompts(self, domain_id: str) -> Dict[str, str]:
        """
        ドメインのプロンプトテンプレート読み込み
        
        Args:
            domain_id: ドメインID（例: "horse-racing"）
        
        Returns:
            プロンプト辞書
            {
                'domain_instructions': '...',
                'data_reliability_guide': '...',
                'analysis_procedure': '...',
                'output_format': '...',
                'key_principles': '...'
            }
        """
        prompts_file = self.config_dir / "domains" / domain_id / "prompts.yaml"
        
        if not prompts_file.exists():
            # プロンプトファイルがない場合は空辞書を返す
            return {}
        
        with open(prompts_file, 'r', encoding='utf-8') as f:
            prompts = yaml.safe_load(f)
        
        return prompts if prompts else {}
    
    def get_active_domain_config(self) -> Dict[str, Any]:
        """アクティブドメイン設定"""
        app_config = self.load_app_config()
        active_domain = app_config['app']['active_domain']
        return self.load_domain_config(active_domain)
    
    def get_active_domain_prompts(self) -> Dict[str, str]:
        """アクティブドメインのプロンプト取得"""
        app_config = self.load_app_config()
        active_domain = app_config['app']['active_domain']
        return self.load_domain_prompts(active_domain)
    
    def clear_cache(self):
        """キャッシュクリア"""
        self._cache.clear()


# グローバルインスタンス
config_loader = ConfigLoader()
app_settings = AppSettings()