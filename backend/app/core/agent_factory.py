"""
エージェントファクトリ
設定からエージェントを動的生成（YAML読み込み版）
"""
from openai import OpenAI
from typing import List, Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)


class AgentFactory:
    """エージェント生成ファクトリ"""
    
    def __init__(self, config_loader, app_settings):
        """
        初期化
        
        Args:
            config_loader: ConfigLoaderインスタンス
            app_settings: AppSettingsインスタンス
        """
        self.config_loader = config_loader
        self.app_settings = app_settings
        
        # 設定読み込み
        self.app_config = config_loader.load_app_config()
        self.agent_config = config_loader.load_agent_config()
        self.domain_config = config_loader.get_active_domain_config()
    
    def create_agent(
        self,
        name: Optional[str] = None,
        tools: Optional[List[Dict]] = None,
        tool_functions: Optional[Dict] = None
    ):
        """
        エージェント生成
        
        Args:
            name: エージェント名（オプション）
            tools: OpenAI Function Calling用のツール定義
            tool_functions: 実行可能な関数マップ
        
        Returns:
            DynamicAgentインスタンス
        """
        # エージェント名
        domain_agent_config = self.domain_config.get('agent', {})
        agent_name = name or domain_agent_config.get('name', 'AssistantAgent')
        
        # 指示文構築
        instructions = self._build_instructions()
        
        # LLM設定
        llm_config = self.app_config['llm']
        
        # エージェント生成
        agent = DynamicAgent(
            name=agent_name,
            model=llm_config['model'],
            instructions=instructions,
            api_key=self.app_settings.OPENAI_API_KEY,
            temperature=llm_config.get('temperature', 0.7),
            max_tokens=llm_config.get('max_tokens', 4000),
            tools=tools or [],
            tool_functions=tool_functions or {}
        )
        
        logger.info(f"Created agent: {agent_name}")
        logger.info(f"Tools: {len(tools or [])}")
        
        return agent
    
    def _build_instructions(self) -> str:
        """
        指示文構築（YAMLから読み込み）
        
        Returns:
            完全な指示文
        """
        parts = []
        
        # 1. 基本指示（agents.config.yamlから）
        default_config = self.agent_config['agents']['default']
        parts.append(default_config['base_instructions'])
        
        # 2. ドメイン設定取得
        domain_agent_config = self.domain_config.get('agent', {})
        
        # 3. プロンプトテンプレート読み込み
        prompts = self.config_loader.get_active_domain_prompts()
        
        # 4. 使用するプロンプトキーを取得
        prompt_keys = domain_agent_config.get('prompt_templates', [])
        
        if prompt_keys and prompts:
            # プロンプトテンプレートから読み込み
            parts.append("\n## ドメイン固有指示\n")
            for key in prompt_keys:
                if key in prompts:
                    parts.append(prompts[key])
                    parts.append("\n")
        else:
            # フォールバック: domain_instructionsから読み込み（旧形式対応）
            domain_instructions = domain_agent_config.get('domain_instructions', '')
            if domain_instructions:
                parts.append("\n## ドメイン固有指示\n")
                parts.append(domain_instructions)
        
        return "\n".join(parts)


class DynamicAgent:
    """動的エージェント（OpenAI Function Calling対応）"""
    
    def __init__(
        self,
        name: str,
        model: str,
        instructions: str,
        api_key: str,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        tools: List[Dict] = None,
        tool_functions: Dict = None
    ):
        """初期化"""
        self.name = name
        self.model = model
        self.instructions = instructions
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tools = tools or []
        self.tool_functions = tool_functions or {}
        
        # OpenAI クライアント
        if not api_key:
            logger.error("OPENAI_API_KEY is not set!")
            raise ValueError("OPENAI_API_KEY is required")
        
        self.client = OpenAI(api_key=api_key)
        
        logger.info(f"DynamicAgent '{name}' initialized with model: {model}")
    
    def chat(self, user_message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        チャット実行（Function Calling対応）
        
        Args:
            user_message: ユーザーメッセージ
            conversation_history: 会話履歴
        
        Returns:
            レスポンス辞書
        """
        logger.info(f"Chat started: {user_message[:50]}...")
        
        # メッセージ構築
        messages = [{"role": "system", "content": self.instructions}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": user_message})
        
        # OpenAI API呼び出し
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=self.tools if self.tools else None,
                tool_choice="auto" if self.tools else None,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            assistant_message = response.choices[0].message
            
            # ツール呼び出しチェック
            if assistant_message.tool_calls:
                logger.info(f"Tool calls detected: {len(assistant_message.tool_calls)}")
                
                # ツール実行
                messages.append(assistant_message)
                
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"Calling tool: {function_name} with args: {function_args}")
                    
                    # ツール実行
                    if function_name in self.tool_functions:
                        function_response = self.tool_functions[function_name](**function_args)
                    else:
                        function_response = {"error": f"Unknown function: {function_name}"}
                    
                    # ツール結果をメッセージに追加
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": json.dumps(function_response, ensure_ascii=False)
                    })
                
                # ツール結果を含めて再度API呼び出し
                second_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                final_message = second_response.choices[0].message.content
                
                return {
                    "response": final_message,
                    "tool_calls": [
                        {
                            "function": tc.function.name,
                            "arguments": json.loads(tc.function.arguments)
                        }
                        for tc in assistant_message.tool_calls
                    ],
                    "usage": second_response.usage.model_dump() if second_response.usage else None
                }
            
            else:
                # ツール呼び出しなし
                logger.info("No tool calls, returning direct response")
                return {
                    "response": assistant_message.content,
                    "tool_calls": [],
                    "usage": response.usage.model_dump() if response.usage else None
                }
        
        except Exception as e:
            logger.error(f"Chat error: {e}")
            raise


# 使用例:
# from app.core.agent_factory import AgentFactory
# from app.core.config import config_loader, app_settings
# from app.core.tool_loader import ToolLoader
#
# tool_loader = ToolLoader(config_loader)
# tools = tool_loader.load_tools()
# tool_functions = tool_loader.get_tool_functions()
#
# agent_factory = AgentFactory(config_loader, app_settings)
# agent = agent_factory.create_agent(tools=tools, tool_functions=tool_functions)