"""
競馬分析ツール（汎用DB接続版）
"""
from typing import Dict, List, Any
import logging

# 汎用DB接続ユーティリティをインポート
from app.core.db_utils import get_db_connection_for_domain

logger = logging.getLogger(__name__)


def get_race_statistics(race_name: str, category: str) -> Dict[str, Any]:
    """
    レース統計データ取得
    
    Args:
        race_name: レース名
        category: 統計カテゴリ
    
    Returns:
        統計データ
    """
    logger.info(f"get_race_statistics called: race_name={race_name}, category={category}")
    
    try:
        # 汎用DB接続関数を使用（自動的にドメインのスキーマを使用）
        conn = get_db_connection_for_domain()
        cursor = conn.cursor()
        
        # 脚質統計はリアルタイム計算
        if category == "running_style":
            result = _get_running_style_stats_dynamic(cursor, race_name)
            conn.close()
            return result
        
        # それ以外（人気・枠順）はDB格納済み統計を取得
        cursor.execute("""
            SELECT 
                condition,
                total_runs,
                wins,
                seconds,
                places,
                win_rate,
                place_rate,
                show_rate,
                years_analyzed
            FROM race_statistics
            WHERE race_name = %s AND category = %s
            ORDER BY 
                CASE 
                    WHEN %s = 'popularity' THEN 
                        CASE condition
                            WHEN '1番人気' THEN 1
                            WHEN '2番人気' THEN 2
                            WHEN '3番人気' THEN 3
                            WHEN '4-6番人気' THEN 4
                            WHEN '7-9番人気' THEN 5
                            WHEN '10番人気以下' THEN 6
                            ELSE 99
                        END
                    WHEN %s = 'post_position' THEN 
                        CASE 
                            WHEN condition ~ '^[0-9]+枠$' THEN 
                                CAST(SUBSTRING(condition FROM '^([0-9]+)') AS INTEGER)
                            ELSE 99
                        END
                    ELSE 99
                END
        """, (race_name, category, category, category))
        
        rows = cursor.fetchall()
        
        if not rows:
            conn.close()
            return {
                "error": f"レース '{race_name}' のカテゴリ '{category}' のデータが見つかりません",
                "race_name": race_name,
                "category": category
            }
        
        # データ整形
        data = []
        for row in rows:
            data.append({
                "condition": row[0],
                "total_runs": row[1],
                "wins": row[2],
                "seconds": row[3],
                "places": row[4],
                "win_rate": float(row[5]) if row[5] else 0,
                "place_rate": float(row[6]) if row[6] else 0,
                "show_rate": float(row[7]) if row[7] else 0,
                "sample_size": row[1]
            })
        
        years_analyzed = rows[0][8] if rows else 10
        
        conn.close()
        
        result = {
            "race_name": race_name,
            "category": category,
            "data": data,
            "years_analyzed": years_analyzed,
            "data_quality": "高信頼性（全頭を加味した統計）",
            "note": "競馬ラボから取得した統計データです"
        }
        
        logger.info(f"Returning {len(data)} records for {race_name}/{category}")
        return result
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "error": f"データベースエラー: {str(e)}",
            "race_name": race_name,
            "category": category
        }


def _get_running_style_stats_dynamic(cursor, race_name: str) -> Dict[str, Any]:
    """脚質統計を動的計算"""
    # ... 既存の実装そのまま ...
    cursor.execute("""
        SELECT 
            estimated_running_style as condition,
            COUNT(*) as total_runs,
            SUM(CASE WHEN finish_position = 1 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN finish_position <= 3 THEN 1 ELSE 0 END) as top3
        FROM race_results rr
        JOIN races r ON rr.race_id = r.race_id
        WHERE r.race_name = %s 
          AND estimated_running_style IS NOT NULL
        GROUP BY estimated_running_style
        ORDER BY CASE estimated_running_style
            WHEN '逃げ' THEN 1
            WHEN '先行' THEN 2
            WHEN '差し' THEN 3
            WHEN '追込' THEN 4
        END
    """, (race_name,))
    
    rows = cursor.fetchall()
    
    if not rows:
        return {
            "error": f"レース '{race_name}' の脚質データが見つかりません",
            "race_name": race_name,
            "category": "running_style"
        }
    
    # データ整形
    data = []
    total_horses = 0
    
    for row in rows:
        condition, total_runs, wins, top3 = row
        total_horses += total_runs
        win_rate = round(wins / total_runs * 100, 1) if total_runs > 0 else 0
        
        data.append({
            "condition": condition,
            "total_runs": total_runs,
            "wins": wins,
            "top3": top3,
            "win_rate": win_rate,
            "sample_size": total_runs
        })
    
    # 警告メッセージ
    data_quality = "参考値"
    warning = None
    
    if total_horses < 100:
        warning = f"データは上位3頭のみのため（サンプル数{total_horses}頭）、統計的信頼性は限定的です。"
        data_quality = "低信頼性（上位3頭のみ）"
    elif total_horses < 150:
        warning = f"サンプル数が少ないため（{total_horses}頭）、統計の信頼性がやや低い可能性があります。"
        data_quality = "中信頼性"
    else:
        data_quality = "高信頼性（全頭データ）"
    
    return {
        "race_name": race_name,
        "category": "running_style",
        "data": data,
        "years_analyzed": 10,
        "total_sample": total_horses,
        "data_quality": data_quality,
        "note": "リアルタイム計算による簡易統計です。",
        "warning": warning
    }


def analyze_elimination_conditions(race_name: str) -> Dict[str, Any]:
    """消去法データ分析"""
    logger.info(f"analyze_elimination_conditions called: race_name={race_name}")
    
    try:
        # 汎用DB接続関数を使用
        conn = get_db_connection_for_domain()
        cursor = conn.cursor()
        
        # ... 既存の実装そのまま（前走人気別・前走着順別） ...
        
        # 前走人気別成績
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN previous_popularity = 1 THEN '前走1番人気'
                    WHEN previous_popularity BETWEEN 2 AND 3 THEN '前走2-3番人気'
                    WHEN previous_popularity BETWEEN 4 AND 6 THEN '前走4-6番人気'
                    ELSE '前走7番人気以下'
                END as condition,
                COUNT(*) as total,
                SUM(CASE WHEN finish_position = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN finish_position <= 3 THEN 1 ELSE 0 END) as top3
            FROM race_results rr
            JOIN races r ON rr.race_id = r.race_id
            WHERE r.race_name = %s AND previous_popularity IS NOT NULL
            GROUP BY condition
            ORDER BY 
                MIN(CASE 
                    WHEN previous_popularity = 1 THEN 1
                    WHEN previous_popularity BETWEEN 2 AND 3 THEN 2
                    WHEN previous_popularity BETWEEN 4 AND 6 THEN 3
                    ELSE 4
                END)
        """, (race_name,))
        
        previous_popularity_data = []
        for row in cursor.fetchall():
            condition, total, wins, top3 = row
            previous_popularity_data.append({
                "condition": condition,
                "total": total,
                "wins": wins,
                "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
                "place_rate": round(top3 / total * 100, 1) if total > 0 else 0,
                "sample_size": total
            })
        
        # 前走着順別成績
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN previous_finish_position = 1 THEN '前走勝利'
                    WHEN previous_finish_position BETWEEN 2 AND 3 THEN '前走2-3着'
                    WHEN previous_finish_position BETWEEN 4 AND 6 THEN '前走4-6着'
                    ELSE '前走7着以下'
                END as condition,
                COUNT(*) as total,
                SUM(CASE WHEN finish_position = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN finish_position <= 3 THEN 1 ELSE 0 END) as top3
            FROM race_results rr
            JOIN races r ON rr.race_id = r.race_id
            WHERE r.race_name = %s AND previous_finish_position IS NOT NULL
            GROUP BY condition
            ORDER BY 
                MIN(CASE 
                    WHEN previous_finish_position = 1 THEN 1
                    WHEN previous_finish_position BETWEEN 2 AND 3 THEN 2
                    WHEN previous_finish_position BETWEEN 4 AND 6 THEN 3
                    ELSE 4
                END)
        """, (race_name,))
        
        previous_finish_data = []
        for row in cursor.fetchall():
            condition, total, wins, top3 = row
            previous_finish_data.append({
                "condition": condition,
                "total": total,
                "wins": wins,
                "win_rate": round(wins / total * 100, 1) if total > 0 else 0,
                "place_rate": round(top3 / total * 100, 1) if total > 0 else 0,
                "sample_size": total
            })
        
        conn.close()
        
        # 重要条件抽出
        key_conditions = []
        for data in previous_popularity_data:
            if data['win_rate'] > 15:
                key_conditions.append(data['condition'])
        for data in previous_finish_data:
            if data['win_rate'] > 15:
                key_conditions.append(data['condition'])
        
        return {
            "race_name": race_name,
            "elimination_data": {
                "previous_popularity": previous_popularity_data,
                "previous_finish_position": previous_finish_data,
                "key_conditions": key_conditions
            },
            "note": "前走条件別の成績データです（上位3頭のみのため参考値）"
        }
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            "error": f"データベースエラー: {str(e)}",
            "race_name": race_name
        }


# ========================================
# ToolLoader用の関数
# ========================================

def get_tools() -> List[Dict[str, Any]]:
    """ツール定義"""
    return [
        {
            "type": "function",
            "function": {
                "name": "get_race_statistics",
                "description": "競馬レースの統計データを取得します。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "race_name": {
                            "type": "string",
                            "description": "レース名"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["popularity", "running_style", "post_position"],
                            "description": "統計カテゴリ"
                        }
                    },
                    "required": ["race_name", "category"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "analyze_elimination_conditions",
                "description": "消去法データを分析します。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "race_name": {
                            "type": "string",
                            "description": "レース名"
                        }
                    },
                    "required": ["race_name"]
                }
            }
        }
    ]


def get_tool_functions() -> Dict[str, Any]:
    """実行可能な関数マップ"""
    return {
        "get_race_statistics": get_race_statistics,
        "analyze_elimination_conditions": analyze_elimination_conditions
    }