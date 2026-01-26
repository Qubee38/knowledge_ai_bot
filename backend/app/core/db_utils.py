"""
データベースユーティリティ
Row Level Security (RLS) 対応
"""
import psycopg2
import psycopg2.extras
from psycopg2.extensions import register_adapter, AsIs
import os
import logging
from typing import Optional, Tuple
from uuid import UUID

logger = logging.getLogger(__name__)

# UUID型をPostgreSQLで扱えるように登録
def adapt_uuid(uuid_value):
    """UUID型をPostgreSQLのUUID型に変換"""
    return AsIs(f"'{str(uuid_value)}'::uuid")

# UUID型アダプター登録
register_adapter(UUID, adapt_uuid)

# 環境変数からデータベースURL取得
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@postgres:5432/knowledge_ai_bot"
)


def get_db_connection(
    schema: Optional[str] = None,
    user_id: Optional[str] = None
) -> Tuple[psycopg2.extensions.connection, psycopg2.extras.RealDictCursor]:
    """
    データベース接続取得
    
    Args:
        schema: スキーマ名（デフォルト: public）
        user_id: ユーザーID（RLS用）
    
    Returns:
        tuple: (connection, cursor)
    """
    try:
        conn = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        cursor = conn.cursor()
        
        # スキーマ設定
        if schema:
            cursor.execute(f"SET search_path TO {schema}, public")
            logger.debug(f"Using schema: {schema}")
        else:
            logger.debug("Using default schema (public)")
        
        # RLS用のユーザーID設定
        if user_id:
            cursor.execute("SET app.current_user_id = %s", (str(user_id),))
            logger.debug(f"Set RLS user_id: {user_id}")
        
        return conn, cursor
        
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise


def close_db_connection(
    conn: Optional[psycopg2.extensions.connection],
    cursor: Optional[psycopg2.extras.RealDictCursor]
):
    """
    データベース接続クローズ
    
    Args:
        conn: データベース接続
        cursor: カーソル
    """
    try:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        logger.debug("Database connection closed")
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")


def execute_query(
    query: str,
    params: Optional[tuple] = None,
    schema: Optional[str] = None,
    user_id: Optional[str] = None,
    fetch_one: bool = False,
    fetch_all: bool = True
):
    """
    クエリ実行ヘルパー関数
    
    Args:
        query: SQLクエリ
        params: クエリパラメータ
        schema: スキーマ名
        user_id: ユーザーID（RLS用）
        fetch_one: 単一行取得
        fetch_all: 全行取得
    
    Returns:
        クエリ結果
    """
    conn = None
    cursor = None
    
    try:
        conn, cursor = get_db_connection(schema=schema, user_id=user_id)
        
        cursor.execute(query, params or ())
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = None
        
        conn.commit()
        
        return result
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Query execution error: {e}")
        raise
    finally:
        close_db_connection(conn, cursor)


def execute_transaction(operations: list, schema: Optional[str] = None):
    """
    トランザクション実行ヘルパー
    
    Args:
        operations: 操作リスト [(query, params), ...]
        schema: スキーマ名
    
    Returns:
        成功フラグ
    """
    conn = None
    cursor = None
    
    try:
        conn, cursor = get_db_connection(schema=schema)
        
        for query, params in operations:
            cursor.execute(query, params or ())
        
        conn.commit()
        logger.debug(f"Transaction completed: {len(operations)} operations")
        
        return True
        
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Transaction error: {e}")
        raise
    finally:
        close_db_connection(conn, cursor)

def get_db_connection_for_domain():
    """
    現在のアクティブドメインに対応したDB接続を取得
    
    domain.yaml の database.schema 設定を読み込み、
    自動的にスキーマを設定した接続を返します。
    
    Returns:
        psycopg2.connection: スキーマ設定済みのDB接続
    
    Raises:
        Exception: スキーマ設定取得失敗時
    """
    try:
        # ConfigLoaderをインポート
        from app.core.config import config_loader
        
        # アクティブドメインの設定を取得
        domain_config = config_loader.get_active_domain_config()
        
        # database.schema 設定を取得
        db_config = domain_config.get('database', {})
        schema_name = db_config.get('schema', 'public')
        use_schema_separation = db_config.get('use_schema_separation', True)
        
        # スキーマ分離が無効の場合は public を使用
        if not use_schema_separation:
            schema_name = 'public'
        
        logger.info(f"Domain DB connection: schema={schema_name}")
        
        # スキーマ設定付きで接続
        conn = psycopg2.connect(
            DATABASE_URL,
            cursor_factory=psycopg2.extras.RealDictCursor
        )
        cursor = conn.cursor()
        
        # search_path 設定
        cursor.execute(f"SET search_path TO {schema_name}, public")
        logger.debug(f"Search path set to: {schema_name}, public")
        
        # カーソルは閉じずに接続だけ返す
        # （ツール側でカーソルを作成する）
        return conn
        
    except Exception as e:
        logger.error(f"Failed to get domain DB connection: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


def get_domain_schema_name() -> str:
    """
    現在のアクティブドメインのスキーマ名を取得
    
    Returns:
        str: スキーマ名（例: "horse_racing"）
    """
    try:
        from app.core.config import config_loader
        
        domain_config = config_loader.get_active_domain_config()
        db_config = domain_config.get('database', {})
        schema_name = db_config.get('schema', 'public')
        use_schema_separation = db_config.get('use_schema_separation', True)
        
        if not use_schema_separation:
            return 'public'
        
        return schema_name
        
    except Exception as e:
        logger.error(f"Failed to get domain schema name: {e}")
        return 'public'