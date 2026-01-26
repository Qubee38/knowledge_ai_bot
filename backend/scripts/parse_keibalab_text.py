#!/usr/bin/env python3
"""
競馬ラボのテキストデータをパースしてPostgreSQLに投入（修正版）
人気データと枠順データの両方に対応
"""
import sys
import os
import psycopg2
import psycopg2.extras
import re
from datetime import datetime
import argparse

# 環境変数からデータベースURL取得
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://postgres:password@postgres:5432/knowledge_ai_bot'
)

# スキーマ名
SCHEMA_NAME = os.getenv('DOMAIN_SCHEMA', 'horse_racing')


def parse_race_results(lines):
    """レース結果をパース"""
    races = []
    current_race = None
    
    for line in lines:
        line = line.strip()
        
        # 年度・レース条件行
        if line.startswith('20') and '年' in line and 'サラ系' in line:
            # 新しいレースの開始
            year_match = re.match(r'(\d{4})年', line)
            if year_match:
                year = year_match.group(1)
                
                # レース条件抽出
                race_class = ''
                if 'サラ系3歳オープン' in line:
                    race_class = 'サラ系3歳オープン'
                
                # 馬場状態
                surface = ''
                track_condition = ''
                weather = ''
                distance = 0
                
                if '芝' in line:
                    surface = '芝'
                    # 距離抽出（例: 芝1600m）
                    distance_match = re.search(r'芝(\d+)m', line)
                    if distance_match:
                        distance = int(distance_match.group(1))
                
                if '良' in line:
                    track_condition = '良'
                elif '稍重' in line:
                    track_condition = '稍重'
                elif '重' in line:
                    track_condition = '重'
                
                if '晴' in line:
                    weather = '晴'
                elif '曇' in line:
                    weather = '曇'
                elif '雨' in line:
                    weather = '雨'
                
                # 出走頭数
                num_horses = 0
                horses_match = re.search(r'(\d+)頭', line)
                if horses_match:
                    num_horses = int(horses_match.group(1))
                
                current_race = {
                    'year': year,
                    'race_class': race_class,
                    'surface': surface,
                    'track_condition': track_condition,
                    'weather': weather,
                    'distance': distance,
                    'num_horses': num_horses
                }
        
        # 日付・開催情報行（例: 1/13 1回中京 5日目）
        elif current_race and re.match(r'\d+/\d+', line):
            date_match = re.match(r'(\d+)/(\d+)', line)
            if date_match:
                month = int(date_match.group(1))
                day = int(date_match.group(2))
                
                # 開催場所抽出
                race_venue = ''
                track_name = ''
                
                if '中京' in line:
                    race_venue_match = re.search(r'(\d+回中京\d+日目)', line)
                    if race_venue_match:
                        race_venue = race_venue_match.group(1)
                    track_name = '中京'
                elif '京都' in line:
                    race_venue_match = re.search(r'(\d+回京都\d+日目)', line)
                    if race_venue_match:
                        race_venue = race_venue_match.group(1)
                    track_name = '京都'
                
                current_race['month'] = month
                current_race['day'] = day
                current_race['race_venue'] = race_venue
                current_race['track_name'] = track_name
                
                races.append(current_race)
                current_race = None
    
    return races


def parse_statistics_section(lines, section_name):
    """統計セクションをパース"""
    data = []
    in_section = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # セクション開始検出
        if section_name in line:
            in_section = True
            continue
        
        # セクション終了検出
        if in_section and (line.startswith('年齢') or line.startswith('所属') or not line):
            break
        
        # データ行をパース
        if in_section and line and not line.startswith('条件'):
            parts = line.split()
            
            # 最低限必要なデータ: 条件名 + 3つ以上の数値
            if len(parts) >= 4:
                condition = parts[0]
                
                # 数値抽出
                try:
                    # 勝率、連対率、複勝率は通常 後ろから3つ
                    win_rate = float(parts[-3])
                    place_rate = float(parts[-2])
                    show_rate = float(parts[-1])
                    
                    data.append({
                        'condition': condition,
                        'win_rate': win_rate,
                        'place_rate': place_rate,
                        'show_rate': show_rate
                    })
                except (ValueError, IndexError):
                    # パースエラーは無視
                    continue
    
    return data


def import_race_data(race_name: str, grade: str, text_file: str, years_analyzed: int = 10):
    """
    テキストファイルからデータをパースしてDB投入
    """
    
    print(f"=== データ投入開始 ===")
    print(f"レース名: {race_name}")
    print(f"グレード: {grade}")
    print(f"テキストファイル: {text_file}")
    print(f"スキーマ: {SCHEMA_NAME}")
    print()
    
    # ファイル読み込み
    try:
        with open(text_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: {text_file}")
        return
    
    # データベース接続
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        cursor = conn.cursor()
        
        # スキーマ設定
        cursor.execute(f"SET search_path TO {SCHEMA_NAME}, public")
        print(f"✓ スキーマ設定: {SCHEMA_NAME}")
        
    except Exception as e:
        print(f"データベース接続エラー: {e}")
        return
    
    try:
        # --- Step 1: レース結果パース ---
        races = parse_race_results(lines)
        print(f"✓ レース結果パース: {len(races)}件")
        
        # レース登録
        for race in races:
            race_date = f"{race['year']}-{race['month']:02d}-{race['day']:02d}"
            
            cursor.execute("""
                INSERT INTO races (
                    race_name, race_date, race_venue, track_name,
                    distance, surface, track_condition, weather,
                    grade, race_class, num_horses
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
            """, (
                race_name, race_date, race.get('race_venue', ''),
                race.get('track_name', ''), race.get('distance', 0),
                race.get('surface', ''), race.get('track_condition', ''),
                race.get('weather', ''), grade, race.get('race_class', ''),
                race.get('num_horses', 0)
            ))
        
        print(f"✓ レース登録完了: {len(races)}件")
        
        # --- Step 2: 人気データパース ---
        print("\n--- 人気データ処理 ---")
        popularity_data = parse_statistics_section(lines, '人気')
        
        if popularity_data:
            print(f"✓ 人気データ発見: {len(popularity_data)}件")
            
            for item in popularity_data:
                # total_runs を推定（仮に10レース分と仮定）
                total_runs = 10
                wins = int(item['win_rate'] * total_runs / 100)
                seconds = int((item['place_rate'] - item['win_rate']) * total_runs / 100)
                places = int((item['show_rate'] - item['place_rate']) * total_runs / 100)
                
                cursor.execute("""
                    INSERT INTO race_statistics (
                        race_name, category, condition,
                        total_runs, wins, seconds, places,
                        win_rate, place_rate, show_rate,
                        years_analyzed, last_updated
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (race_name, category, condition) 
                    DO UPDATE SET
                        win_rate = EXCLUDED.win_rate,
                        place_rate = EXCLUDED.place_rate,
                        show_rate = EXCLUDED.show_rate,
                        last_updated = CURRENT_TIMESTAMP
                """, (
                    race_name, 'popularity', item['condition'],
                    total_runs, wins, seconds, places,
                    item['win_rate'], item['place_rate'], item['show_rate'],
                    years_analyzed
                ))
                
                print(f"  - {item['condition']}: 勝率{item['win_rate']}% 連対率{item['place_rate']}% 複勝率{item['show_rate']}%")
        else:
            print("⚠ 人気データが見つかりませんでした")
        
        # --- Step 3: 枠順データパース ---
        print("\n--- 枠順データ処理 ---")
        post_position_data = parse_statistics_section(lines, '枠順')
        
        if post_position_data:
            print(f"✓ 枠順データ発見: {len(post_position_data)}件")
            
            for item in post_position_data:
                total_runs = 20
                wins = int(item['win_rate'] * total_runs / 100)
                seconds = int((item['place_rate'] - item['win_rate']) * total_runs / 100)
                places = int((item['show_rate'] - item['place_rate']) * total_runs / 100)
                
                cursor.execute("""
                    INSERT INTO race_statistics (
                        race_name, category, condition,
                        total_runs, wins, seconds, places,
                        win_rate, place_rate, show_rate,
                        years_analyzed, last_updated
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (race_name, category, condition) 
                    DO UPDATE SET
                        win_rate = EXCLUDED.win_rate,
                        place_rate = EXCLUDED.place_rate,
                        show_rate = EXCLUDED.show_rate,
                        last_updated = CURRENT_TIMESTAMP
                """, (
                    race_name, 'post_position', item['condition'],
                    total_runs, wins, seconds, places,
                    item['win_rate'], item['place_rate'], item['show_rate'],
                    years_analyzed
                ))
                
                print(f"  - {item['condition']}: 勝率{item['win_rate']}% 連対率{item['place_rate']}% 複勝率{item['show_rate']}%")
        else:
            print("⚠ 枠順データが見つかりませんでした")
        
        # コミット
        conn.commit()
        
        # 最終確認
        cursor.execute("SELECT COUNT(*) FROM races WHERE race_name = %s", (race_name,))
        races_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) FROM race_statistics WHERE race_name = %s", (race_name,))
        stats_count = cursor.fetchone()['count']
        
        print(f"\n=== データ投入完了 ===")
        print(f"✓ レース: {races_count}件")
        print(f"✓ 統計データ: {stats_count}件")
        print()
        
    except Exception as e:
        conn.rollback()
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cursor.close()
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='競馬ラボのテキストデータをDBに投入')
    parser.add_argument('--input', required=True, help='入力テキストファイル')
    parser.add_argument('--race-name', required=True, help='レース名')
    parser.add_argument('--grade', default='G3', help='グレード（デフォルト: G3）')
    parser.add_argument('--years', type=int, default=10, help='集計年数（デフォルト: 10）')
    parser.add_argument('--schema', default='horse_racing', help='スキーマ名（デフォルト: horse_racing）')
    
    args = parser.parse_args()
    
    global SCHEMA_NAME
    SCHEMA_NAME = args.schema
    
    import_race_data(
        race_name=args.race_name,
        grade=args.grade,
        text_file=args.input,
        years_analyzed=args.years
    )


if __name__ == '__main__':
    main()