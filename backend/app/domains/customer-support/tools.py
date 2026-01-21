"""
カスタマーサポートツール（スタブ実装）

このファイルは app/domains/customer_support/tools.py に配置されます。
実際の実装では、データベースやAPIと連携します。
"""
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def search_knowledge_base(query: str) -> Dict[str, Any]:
    """
    ナレッジベース検索（スタブ実装）
    
    Args:
        query: 検索クエリ
    
    Returns:
        検索結果
    """
    logger.info(f"search_knowledge_base called: query={query}")
    
    # スタブデータ
    stub_results = {
        "配送": {
            "title": "配送に関するFAQ",
            "content": "通常、ご注文から3-5営業日でお届けします。配送状況は追跡番号で確認できます。",
            "related_articles": ["配送料について", "配送先変更方法"]
        },
        "返品": {
            "title": "返品・交換ポリシー",
            "content": "商品到着後30日以内であれば、未使用品に限り返品可能です。",
            "related_articles": ["返品手順", "返金について"]
        },
        "ログイン": {
            "title": "ログイン問題の解決",
            "content": "パスワードをお忘れの場合は、ログイン画面の「パスワードを忘れた方」からリセットできます。",
            "related_articles": ["パスワードリセット", "アカウントロック解除"]
        }
    }
    
    # 簡易検索
    for keyword, result in stub_results.items():
        if keyword in query:
            return {
                "found": True,
                "article": result,
                "confidence": 0.9
            }
    
    return {
        "found": False,
        "message": "該当する記事が見つかりませんでした。詳細をお伺いできますか？"
    }


def create_ticket(
    subject: str,
    description: str,
    priority: str = "normal",
    category: str = "general"
) -> Dict[str, Any]:
    """
    サポートチケット作成（スタブ実装）
    
    Args:
        subject: チケット件名
        description: 詳細説明
        priority: 優先度（low, normal, high, urgent）
        category: カテゴリ（general, technical, billing, shipping）
    
    Returns:
        作成されたチケット情報
    """
    logger.info(f"create_ticket called: subject={subject}, priority={priority}")
    
    # スタブ: チケットID生成
    import random
    ticket_id = f"TKT-{random.randint(10000, 99999)}"
    
    return {
        "success": True,
        "ticket_id": ticket_id,
        "subject": subject,
        "priority": priority,
        "category": category,
        "status": "open",
        "estimated_response_time": "24時間以内",
        "message": f"チケット {ticket_id} を作成しました。担当者が確認次第、ご連絡いたします。"
    }


def check_order_status(order_id: str) -> Dict[str, Any]:
    """
    注文状況確認（スタブ実装）
    
    Args:
        order_id: 注文番号
    
    Returns:
        注文状況
    """
    logger.info(f"check_order_status called: order_id={order_id}")
    
    # スタブデータ
    stub_orders = {
        "12345": {
            "order_id": "12345",
            "status": "配送中",
            "tracking_number": "1234567890",
            "estimated_delivery": "2026-01-18",
            "items": [
                {"name": "商品A", "quantity": 2},
                {"name": "商品B", "quantity": 1}
            ],
            "shipping_address": "東京都〇〇区..."
        },
        "67890": {
            "order_id": "67890",
            "status": "準備中",
            "tracking_number": None,
            "estimated_delivery": "2026-01-20",
            "items": [
                {"name": "商品C", "quantity": 1}
            ],
            "shipping_address": "大阪府〇〇市..."
        }
    }
    
    if order_id in stub_orders:
        return {
            "found": True,
            "order": stub_orders[order_id]
        }
    else:
        return {
            "found": False,
            "message": f"注文番号 {order_id} が見つかりませんでした。もう一度ご確認ください。"
        }


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
        {
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "社内ナレッジベースを検索して、お客様の問い合わせに関連する情報を取得します。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "検索クエリ（例: '配送遅延', '返品方法', 'ログイン問題'）"
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_ticket",
                "description": "サポートチケットを作成します。専門担当者への引き継ぎが必要な場合に使用します。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "subject": {
                            "type": "string",
                            "description": "チケット件名"
                        },
                        "description": {
                            "type": "string",
                            "description": "問題の詳細説明"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "normal", "high", "urgent"],
                            "description": "優先度"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["general", "technical", "billing", "shipping"],
                            "description": "カテゴリ"
                        }
                    },
                    "required": ["subject", "description"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_order_status",
                "description": "注文番号から配送状況を確認します。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "注文番号（例: '12345'）"
                        }
                    },
                    "required": ["order_id"]
                }
            }
        }
    ]


def get_tool_functions() -> Dict[str, Any]:
    """
    実行可能な関数マップを返す
    
    Returns:
        関数マップ {'function_name': function}
    """
    return {
        "search_knowledge_base": search_knowledge_base,
        "create_ticket": create_ticket,
        "check_order_status": check_order_status
    }