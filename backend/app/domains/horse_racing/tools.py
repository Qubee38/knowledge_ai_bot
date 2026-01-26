"""
競馬ドメイン固有ツール
"""
import logging
import traceback
from typing import List, Dict, Any

from app.core.db_utils import get_db_connection_for_domain

logger = logging.getLogger(__name__)


def get_race_statistics(race_name: str, category: str) -> List[Dict[str, Any]]:
    """
    レース統計データ取得
    
    Args:
        race_name: レース名（例: "シンザン記念"）
        category: カテゴリ（popularity, post_position, running_style）
    
    Returns:
        統計データリスト
    """
    logger.info(f"get_race_statistics called: race_name={race_name}, category={category}")
    
    conn = None
    cursor = None
    
    try:
        # ドメイン用DB接続取得
        conn = get_db_connection_for_domain()
        cursor = conn.cursor()
        
        # クエリ実行
        cursor.execute("""
            SELECT 
                condition,
                total_runs,
                wins,
                seconds,
                places,
                win_rate,
                place_rate,
                show_rate
            FROM race_statistics
            WHERE race_name = %s
              AND category = %s
            ORDER BY 
                CASE 
                    WHEN category = 'popularity' THEN 
                        CASE 
                            WHEN condition = '1人気' THEN 1
                            WHEN condition = '2人気' THEN 2
                            WHEN condition = '3人気' THEN 3
                            WHEN condition LIKE '%〜%' THEN 
                                CAST(SUBSTRING(condition FROM '\\d+') AS INTEGER)
                            ELSE 99
                        END
                    WHEN category = 'post_position' THEN 
                        CAST(condition AS INTEGER)
                    ELSE condition
                END
        """, (race_name, category))
        
        rows = cursor.fetchall()
        
        # RealDictCursor を使っているので、辞書形式でアクセス
        results = []
        for row in rows:
            results.append({
                "condition": row['condition'],
                "total_runs": row['total_runs'],
                "wins": row['wins'],
                "seconds": row['seconds'],
                "places": row['places'],
                "win_rate": float(row['win_rate']) if row['win_rate'] else 0.0,
                "place_rate": float(row['place_rate']) if row['place_rate'] else 0.0,
                "show_rate": float(row['show_rate']) if row['show_rate'] else 0.0
            })
        
        logger.info(f"Returning {len(results)} records for {race_name}/{category}")
        
        return results
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        logger.error(traceback.format_exc())
        return []
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def analyze_elimination_conditions(race_name: str) -> Dict[str, Any]:
    """
    消去法データ分析
    
    Args:
        race_name: レース名
    
    Returns:
        消去法データ（前走条件別成績）
    """
    logger.info(f"analyze_elimination_conditions called: race_name={race_name}")
    
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection_for_domain()
        cursor = conn.cursor()
        
        # 前走人気別成績（race_results テーブルから集計）
        cursor.execute("""
            SELECT 
                previous_popularity,
                COUNT(*) as total,
                SUM(CASE WHEN finish_position = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN finish_position <= 3 THEN 1 ELSE 0 END) as places
            FROM race_results rr
            JOIN races r ON rr.race_id = r.race_id
            WHERE r.race_name = %s
              AND previous_popularity IS NOT NULL
            GROUP BY previous_popularity
            ORDER BY previous_popularity
        """, (race_name,))
        
        previous_popularity_rows = cursor.fetchall()
        previous_popularity_data = []
        
        for row in previous_popularity_rows:
            total = row['total']
            wins = row['wins']
            places = row['places']
            
            previous_popularity_data.append({
                'condition': f"前走{row['previous_popularity']}番人気",
                'total': total,
                'wins': wins,
                'win_rate': round(wins / total * 100, 1) if total > 0 else 0,
                'place_rate': round(places / total * 100, 1) if total > 0 else 0
            })
        
        # 前走着順別成績
        cursor.execute("""
            SELECT 
                previous_finish_position,
                COUNT(*) as total,
                SUM(CASE WHEN finish_position = 1 THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN finish_position <= 3 THEN 1 ELSE 0 END) as places
            FROM race_results rr
            JOIN races r ON rr.race_id = r.race_id
            WHERE r.race_name = %s
              AND previous_finish_position IS NOT NULL
            GROUP BY previous_finish_position
            ORDER BY previous_finish_position
        """, (race_name,))
        
        previous_finish_rows = cursor.fetchall()
        previous_finish_data = []
        
        for row in previous_finish_rows:
            total = row['total']
            wins = row['wins']
            places = row['places']
            
            previous_finish_data.append({
                'condition': f"前走{row['previous_finish_position']}着",
                'total': total,
                'wins': wins,
                'win_rate': round(wins / total * 100, 1) if total > 0 else 0,
                'place_rate': round(places / total * 100, 1) if total > 0 else 0
            })
        
        result = {
            'previous_popularity': previous_popularity_data,
            'previous_finish_position': previous_finish_data
        }
        
        logger.info(f"Returning elimination data for {race_name}")
        
        return result
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        logger.error(traceback.format_exc())
        return {
            'previous_popularity': [],
            'previous_finish_position': []
        }
    
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()