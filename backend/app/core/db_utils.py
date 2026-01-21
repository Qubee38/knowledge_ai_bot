"""
データベース接続ユーティリティ（スキーマ分離対応版）

ドメインごとにスキーマを分離してデータを管理
"""
import os
import psycopg2
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# 環境変数からDATABASE_URL取得
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    logger.warning("DATABASE_URL is not set, using default")
    DATABASE_URL = 'postgresql://postgres:password@postgres:5432/knowledge_ai_bot'


def get_db_connection(schema: Optional[str] = None):
    """
    データベース接続取得
    
    Args:
        schema: PostgreSQLスキーマ名（指定しない場合はpublic）
                例: 'horse_racing', 'customer_support'
    
    Returns:
        psycopg2接続オブジェクト
    
    Example:
        # デフォルト（public）スキーマ使用
        conn = get_db_connection()
        
        # 競馬ドメインスキーマ使用
        conn = get_db_connection(schema='horse_racing')
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        
        if schema:
            cursor = conn.cursor()
            # スキーマ設定（フォールバックでpublicも検索パスに含める）
            cursor.execute(f"SET search_path TO {schema}, public")
            logger.info(f"Database schema set to: {schema} (fallback: public)")
        else:
            logger.info("Using default schema (public)")
        
        return conn
    
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


def get_db_connection_for_domain():
    """
    現在のアクティブドメイン用のDB接続取得
    
    ドメイン設定から自動的にスキーマを判定して接続。
    設定がない場合はpublicスキーマを使用。
    
    Returns:
        psycopg2接続オブジェクト
    """
    try:
        from app.core.config import config_loader
        
        # アクティブドメイン取得
        domain_config = config_loader.get_active_domain_config()
        domain_name = domain_config['domain']['name']
        
        # データベース設定確認
        db_config = domain_config.get('database', {})
        
        # スキーマ分離を使用するか確認
        use_schema = db_config.get('use_schema_separation', True)
        
        if not use_schema:
            logger.info(f"Domain '{domain_name}': Using public schema (schema separation disabled)")
            return get_db_connection()
        
        # スキーマ名取得
        if 'schema' in db_config:
            # 明示的に指定されたスキーマ名
            schema = db_config['schema']
        else:
            # ドメインIDからスキーマ名を自動生成
            domain_id = domain_config['domain']['id']
            schema = domain_id.replace('-', '_')
        
        logger.info(f"Domain '{domain_name}': Using schema '{schema}'")
        return get_db_connection(schema=schema)
    
    except ImportError:
        logger.warning("config_loader not available, using default connection (public schema)")
        return get_db_connection()
    except Exception as e:
        logger.error(f"Failed to get domain-specific connection: {e}")
        logger.warning("Falling back to public schema")
        # フォールバック: public スキーマ
        return get_db_connection()


def get_db():
    """
    後方互換性のためのエイリアス
    get_db_connection()と同じ
    """
    return get_db_connection()


# ========================================
# ユーティリティ関数
# ========================================

def create_schema_if_not_exists(schema_name: str):
    """
    スキーマが存在しない場合は作成
    
    Args:
        schema_name: スキーマ名
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        conn.commit()
        
        logger.info(f"Schema '{schema_name}' ensured to exist")
        
        conn.close()
    except Exception as e:
        logger.error(f"Failed to create schema '{schema_name}': {e}")
        raise


def list_schemas():
    """
    データベース内の全スキーマを取得
    
    Returns:
        スキーマ名のリスト
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT schema_name 
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name
        """)
        
        schemas = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return schemas
    except Exception as e:
        logger.error(f"Failed to list schemas: {e}")
        return []


def get_tables_in_schema(schema_name: str):
    """
    指定スキーマ内のテーブル一覧を取得
    
    Args:
        schema_name: スキーマ名
    
    Returns:
        テーブル名のリスト
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tablename 
            FROM pg_tables
            WHERE schemaname = %s
            ORDER BY tablename
        """, (schema_name,))
        
        tables = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return tables
    except Exception as e:
        logger.error(f"Failed to get tables in schema '{schema_name}': {e}")
        return []