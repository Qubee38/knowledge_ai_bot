"""
ツールローダー
ドメインからツールを動的に読み込む（Function Calling対応）
"""
import importlib
from typing import List, Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


class ToolLoader:
    """ツール動的ローダー"""
    
    def __init__(self, config_loader):
        """
        初期化
        
        Args:
            config_loader: ConfigLoaderインスタンス
        """
        self.config_loader = config_loader
        self.domain_config = config_loader.get_active_domain_config()
    
    def load_tools(self) -> List[Dict[str, Any]]:
        """
        ドメイン設定から使用するツールをロード
        
        Returns:
            OpenAI Function Calling用のツール定義リスト
            [
                {
                    "type": "function",
                    "function": {
                        "name": "get_race_statistics",
                        "description": "...",
                        "parameters": {...}
                    }
                },
                ...
            ]
        """
        domain_id = self.domain_config['domain']['id']
        
        try:
            # domains/{domain_id}/tools.py を動的インポート
            module_name = f"app.domains.{domain_id.replace('-', '_')}.tools"
            module = importlib.import_module(module_name)
            
            # get_tools() でツール定義取得
            if hasattr(module, 'get_tools'):
                tools = module.get_tools()
                logger.info(f"Loaded {len(tools)} tools from {module_name}")
                return tools
            
            # TOOL_DEFINITIONS が存在する場合（旧形式対応）
            elif hasattr(module, 'TOOL_DEFINITIONS'):
                tools = module.TOOL_DEFINITIONS
                logger.info(f"Loaded {len(tools)} tools from {module_name} (legacy format)")
                return tools
            
            else:
                logger.warning(f"No tools found in {module_name}")
                return []
        
        except ImportError as e:
            logger.error(f"Failed to import tools module: {e}")
            return []
    
    def get_tool_functions(self) -> Dict[str, Callable]:
        """
        実行可能な関数マップを取得
        
        Returns:
            {'get_race_statistics': function, ...}
        """
        domain_id = self.domain_config['domain']['id']
        
        try:
            # domains/{domain_id}/tools.py を動的インポート
            module_name = f"app.domains.{domain_id.replace('-', '_')}.tools"
            module = importlib.import_module(module_name)
            
            # get_tool_functions() で関数マップ取得
            if hasattr(module, 'get_tool_functions'):
                functions = module.get_tool_functions()
                logger.info(f"Loaded {len(functions)} tool functions from {module_name}")
                return functions
            
            # TOOL_FUNCTIONS が存在する場合（旧形式対応）
            elif hasattr(module, 'TOOL_FUNCTIONS'):
                functions = module.TOOL_FUNCTIONS
                logger.info(f"Loaded {len(functions)} tool functions from {module_name} (legacy format)")
                return functions
            
            else:
                logger.warning(f"No tool functions found in {module_name}")
                return {}
        
        except ImportError as e:
            logger.error(f"Failed to import tools module: {e}")
            return {}
    
    def get_enabled_tools(self) -> List[str]:
        """
        有効なツール名のリストを取得
        
        Returns:
            ['get_race_statistics', 'analyze_elimination_conditions']
        """
        tools_config = self.domain_config.get('tools', {})
        enabled = tools_config.get('enabled', [])
        return enabled


# 使用例:
# from app.core.tool_loader import ToolLoader
# tool_loader = ToolLoader(config_loader)
# tools = tool_loader.load_tools()
# tool_functions = tool_loader.get_tool_functions()