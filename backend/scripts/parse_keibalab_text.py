#!/usr/bin/env python3
"""
競馬ラボテキストデータパーサー（完全版）
テキストデータを直接パースしてデータベースに投入

方針A: 脚質統計はDB格納せず、リアルタイム計算
"""
import re
import argparse
import psycopg2
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/knowledge_ai_bot')
SCHEMA_NAME = 'horse_racing'  # 追加


class FieldMapper:
    """フィールドマッピング定義"""
    
    # 通常の結果行（2着以降）
    NORMAL = {
        'finish': 0,
        'gate': 1,
        'horse': 2,
        'age_sex': 3,
        'popularity': 4,
        'jockey': 5,
        'jockey_weight': 6,
        'trainer': 7,
        'time': 8,
        'last_3f': 9,
        'body_weight': 10,
        'passing': 11,
        'sire': 12,
        'dam_sire': 13,
        'prev_race': 14,
        'interval': 15,
        'prev_popularity': 16,
        'prev_finish': 17
    }
    
    # 1着馬（日目情報から抽出）
    WINNER = {
        'gate': 0,
        'horse': 1,
        'age_sex': 2,
        'popularity': 3,
        'jockey': 4,
        'jockey_weight': 5,
        'trainer': 6,
        'time': 7,
        'last_3f': 8,
        'body_weight': 9,
        'passing': 10,
        'sire': 11,
        'dam_sire': 12,
        'prev_race': 13,
        'interval': 14,
        'prev_popularity': 15,
        'prev_finish': 16
    }


class KeibaLabTextParser:
    """競馬ラボテキストパーサー"""
    
    def __init__(self, text_data: str, race_name: str, grade: str, debug: bool = False):
        self.lines = [line.rstrip() for line in text_data.strip().split('\n')]
        self.current_line = 0
        self.race_name = race_name
        self.grade = grade
        self.debug = debug
        
        # パース結果格納
        self.races = []
        self.race_results = []
        self.statistics = {'post_position': [], 'popularity': []}
    
    def _debug_print(self, msg: str):
        """デバッグ出力"""
        if self.debug:
            print(f"[DEBUG] {msg}")
    
    @staticmethod
    def estimate_running_style(passing_positions: str) -> Optional[str]:
        """通過順位から脚質を判定"""
        if not passing_positions or passing_positions.strip() == '':
            return None
        
        position_map = {
            '①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5,
            '⑥': 6, '⑦': 7, '⑧': 8, '⑨': 9, '⑩': 10,
            '⑪': 11, '⑫': 12, '⑬': 13, '⑭': 14, '⑮': 15,
            '⑯': 16, '⑰': 17, '⑱': 18
        }
        
        position_chars = re.findall(r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱]', passing_positions)
        
        if not position_chars:
            return None
        
        positions = [position_map[char] for char in position_chars]
        num_positions = len(positions)
        
        # 逃げ判定
        if num_positions >= 4:
            if all(pos == 1 for pos in positions[-3:]):
                return "逃げ"
        elif num_positions == 3:
            if all(pos == 1 for pos in positions):
                return "逃げ"
        elif num_positions == 2:
            if all(pos == 1 for pos in positions):
                return "逃げ"
        
        fourth_corner = positions[-1]
        
        if 1 <= fourth_corner <= 5:
            return "先行"
        elif 6 <= fourth_corner <= 10:
            return "差し"
        else:
            return "追込"
    
    @staticmethod
    def parse_time_to_seconds(time_str: str) -> Optional[float]:
        """タイム文字列を秒数に変換"""
        if not time_str or time_str.strip() == '':
            return None
        
        try:
            parts = time_str.split(':')
            if len(parts) == 2:
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(time_str)
        except:
            return None
    
    @staticmethod
    def parse_weight_info(weight_str: str) -> Tuple[Optional[int], Optional[int]]:
        """馬体重情報をパース"""
        if not weight_str:
            return None, None
        
        match = re.match(r'(\d+)\(([＋－])(\d+)\)', weight_str)
        if match:
            weight = int(match.group(1))
            sign = match.group(2)
            change = int(match.group(3))
            change = change if sign == '＋' else -change
            return weight, change
        
        match = re.match(r'(\d+)', weight_str)
        if match:
            return int(match.group(1)), 0
        
        return None, None
    
    @staticmethod
    def parse_interval(interval_str: str) -> Optional[int]:
        """間隔文字列をパース"""
        if not interval_str:
            return None
        
        match = re.search(r'(\d+)週', interval_str)
        if match:
            weeks = int(match.group(1))
            return weeks * 7
        
        match = re.search(r'(\d+)ヶ月', interval_str)
        if match:
            months = int(match.group(1))
            return months * 30
        
        return None
    
    @staticmethod
    def safe_int(value: str) -> Optional[int]:
        """安全なint変換"""
        if not value or not value.strip():
            return None
        try:
            return int(value)
        except ValueError:
            return None
    
    @staticmethod
    def safe_float(value: str) -> Optional[float]:
        """安全なfloat変換"""
        if not value or not value.strip():
            return None
        try:
            return float(value)
        except ValueError:
            return None
    
    def parse(self):
        """メインパース処理"""
        print(f"パース開始: {self.race_name}")
        
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line]
            
            if self._is_year_header(line):
                self._debug_print(f"年度ヘッダー検出: {line[:50]}")
                self._parse_race_block()
            elif self._is_statistics_section(line):
                self._debug_print("統計セクション検出")
                self._parse_statistics()
            else:
                self.current_line += 1
        
        print(f"パース完了: レース={len(self.races)}件, 結果={len(self.race_results)}件")
    
    def _is_year_header(self, line: str) -> bool:
        """年度ヘッダー判定"""
        return re.match(r'^\d{4}年', line) is not None
    
    def _is_statistics_section(self, line: str) -> bool:
        """統計セクション判定"""
        return line.strip() == '条件別成績'
    
    def _parse_race_block(self):
        """レースブロック解析"""
        year_line = self.lines[self.current_line]
        race_info = self._parse_race_header(year_line)
        
        self.current_line += 1
        date_info, first_result_line = self._parse_date_and_venue()
        
        race_info.update(date_info)
        
        # レース結果行を解析
        results = []
        
        # 1着馬が日目情報に含まれていた場合
        if first_result_line:
            self._debug_print(f"1着馬データ行: {first_result_line[:80]}")
            first_result = self._parse_winner_row(first_result_line)
            if first_result:
                results.append(first_result)
                self._debug_print(f"1着馬パース成功: {first_result['horse_name']}")
            else:
                self._debug_print("1着馬パース失敗")
        
        result_count = len(results)
        
        # 2着以降のレース結果を解析
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line]
            
            # 空行チェック
            if not line.strip():
                self._debug_print(f"空行でレース結果終了 (results={result_count})")
                break
            
            # 次の年度ヘッダーチェック
            if self._is_year_header(line):
                self._debug_print(f"次の年度ヘッダー検出でレース結果終了 (results={result_count})")
                break
            
            # 統計セクションチェック
            if self._is_statistics_section(line):
                self._debug_print(f"統計セクション検出でレース結果終了 (results={result_count})")
                break
            
            # タブ区切りの行 = レース結果
            if '\t' in line:
                result = self._parse_normal_row(line)
                if result:
                    results.append(result)
                    result_count += 1
                    self._debug_print(f"{result['finish_position']}着: {result['horse_name']} ({result_count}頭目)")
                self.current_line += 1
            else:
                # タブがない行は読み飛ばす
                self._debug_print(f"タブなし行スキップ: {line[:30]}")
                self.current_line += 1
        
        if race_info.get('year'):
            self.races.append(race_info)
            self.race_results.extend(results)
            print(f"  {race_info['year']}年: {len(results)}頭")
        else:
            self._debug_print("年度情報なしのためスキップ")
    
    def _parse_race_header(self, line: str) -> Dict:
        """レースヘッダー情報抽出"""
        year_match = re.match(r'^(\d{4})年', line)
        year = int(year_match.group(1)) if year_match else None
        
        race_class_match = re.search(r'年\s+([^\(]+)', line)
        race_class = race_class_match.group(1).strip() if race_class_match else None
        
        weather_match = re.search(r'(晴|曇|雨)', line)
        weather = weather_match.group(1) if weather_match else None
        
        condition_match = re.search(r'(良|稍重|重|不良)', line)
        track_condition = condition_match.group(1) if condition_match else None
        
        distance_match = re.search(r'([芝ダート])(\d+)m', line)
        if distance_match:
            surface = distance_match.group(1)
            distance = int(distance_match.group(2))
        else:
            surface = None
            distance = None
        
        horses_match = re.search(r'(\d+)頭', line)
        num_horses = int(horses_match.group(1)) if horses_match else None
        
        return {
            'year': year,
            'race_class': race_class,
            'weather': weather,
            'track_condition': track_condition,
            'surface': surface,
            'distance': distance,
            'num_horses': num_horses
        }
    
    def _parse_date_and_venue(self) -> Tuple[Dict, Optional[str]]:
        """日付・開催情報解析"""
        date_str = None
        venue = None
        track_name = None
        first_result_line = None
        
        # 次の数行を確認（最大5行）
        for i in range(5):
            if self.current_line >= len(self.lines):
                break
            
            line = self.lines[self.current_line]
            
            # 空行はスキップ
            if not line.strip():
                self.current_line += 1
                continue
            
            # 日付（M/D形式）
            if re.match(r'^\d{1,2}/\d{1,2}$', line.strip()):
                date_str = line.strip()
                self._debug_print(f"日付検出: {date_str}")
                self.current_line += 1
            # 開催情報（"1回中京"等）
            elif re.match(r'^\d+回', line.strip()):
                venue_match = re.match(r'^(\d+回)(.+)$', line.strip())
                if venue_match:
                    venue = venue_match.group(1) + venue_match.group(2)
                    track_name = venue_match.group(2)
                    self._debug_print(f"開催情報検出: {venue}")
                self.current_line += 1
            # 日目情報（重要：タブがある場合は1着馬データが含まれている）
            elif re.match(r'^\d+日目', line):
                # タブで分割
                if '\t' in line:
                    # 日目情報部分と1着馬データ部分を分離
                    parts = line.split('\t', 1)
                    day_info = parts[0]
                    
                    # 日目情報を追加
                    if venue:
                        venue += day_info
                        self._debug_print(f"日目情報検出: {venue}")
                    
                    # 1着馬データ行を保存
                    if len(parts) > 1:
                        first_result_line = parts[1]
                        self._debug_print(f"1着馬データ検出（先頭80文字）: {first_result_line[:80]}")
                else:
                    # タブがない場合は通常の日目情報
                    if venue:
                        venue += line.strip()
                        self._debug_print(f"日目情報追加: {venue}")
                
                self.current_line += 1
                # 日目情報の後は終了
                break
            else:
                # その他の行
                self._debug_print(f"日付・開催情報終了: {line[:30]}")
                break
        
        return {
            'date_str': date_str,
            'venue': venue,
            'track_name': track_name
        }, first_result_line
    
    def _parse_winner_row(self, row: str) -> Optional[Dict]:
        """1着馬データ行をパース"""
        fields = row.split('\t')
        
        self._debug_print(f"1着馬フィールド数: {len(fields)}")
        if self.debug and len(fields) > 0:
            for i, field in enumerate(fields[:min(10, len(fields))]):
                self._debug_print(f"  [{i}] = {field}")
        
        if len(fields) < 11:
            self._debug_print(f"フィールド数不足（1着馬）: {len(fields)}個")
            return None
        
        try:
            # フィールド構造の自動判定
            # 最初のフィールドが数字かどうかで判定
            first_is_number = self.safe_int(fields[0]) is not None
            
            if first_is_number:
                # パターン1: [枠, 馬名, 齢性, 人気, ...]
                fm = FieldMapper.WINNER
            else:
                # パターン2: [馬名, 齢性, 人気, ...] (枠なし)
                # この場合、全フィールドを1つずつシフト
                fm = {k: v - 1 if v > 0 else v for k, v in FieldMapper.WINNER.items()}
                fm['gate'] = None  # 枠なし
            
            # 馬齢・性別分離
            age_sex_idx = fm['age_sex'] if fm['age_sex'] is not None else 1
            age_sex_match = re.match(r'([牡牝セ])(\d+)', fields[age_sex_idx]) if age_sex_idx < len(fields) else None
            if age_sex_match:
                sex = age_sex_match.group(1)
                age = int(age_sex_match.group(2))
            else:
                sex = None
                age = None
            
            # 各フィールド取得（安全に）
            def get_field(key):
                idx = fm.get(key)
                if idx is None or idx >= len(fields):
                    return None
                return fields[idx] if fields[idx] else None
            
            # 馬体重パース
            weight, weight_change = self.parse_weight_info(get_field('body_weight') or '')
            
            # 間隔パース
            interval_days = self.parse_interval(get_field('interval') or '')
            
            # 脚質推定
            running_style = self.estimate_running_style(get_field('passing') or '')
            
            # タイム変換
            time_seconds = self.parse_time_to_seconds(get_field('time') or '')
            
            result = {
                'finish_position': 1,  # 1着固定
                'gate_number': self.safe_int(get_field('gate')),
                'horse_name': get_field('horse'),
                'age': age,
                'sex': sex,
                'popularity': self.safe_int(get_field('popularity')),
                'jockey_name': get_field('jockey'),
                'jockey_weight': self.safe_float(get_field('jockey_weight')),
                'trainer_name': get_field('trainer'),
                'final_time': get_field('time'),
                'final_time_seconds': time_seconds,
                'last_3f_time': self.safe_float(get_field('last_3f')),
                'weight': weight,
                'weight_change': weight_change,
                'passing_positions': get_field('passing'),
                'estimated_running_style': running_style,
                'sire': get_field('sire'),
                'broodmare_sire': get_field('dam_sire'),
                'previous_race': get_field('prev_race'),
                'days_since_last_race': interval_days,
                'previous_popularity': self.safe_int(get_field('prev_popularity')),
                'previous_finish_position': self.safe_int(get_field('prev_finish'))
            }
            
            return result
            
        except Exception as e:
            self._debug_print(f"結果パースエラー（1着馬）: {e}")
            if self.debug:
                import traceback
                self._debug_print(traceback.format_exc())
            return None
    
    def _parse_normal_row(self, row: str) -> Optional[Dict]:
        """通常の結果行をパース（2着以降）"""
        fields = row.split('\t')
        fm = FieldMapper.NORMAL
        
        if len(fields) < 12:
            self._debug_print(f"フィールド数不足: {len(fields)}個")
            return None
        
        try:
            # 各フィールド取得（安全に）
            def get_field(key):
                idx = fm.get(key)
                if idx is None or idx >= len(fields):
                    return None
                return fields[idx] if fields[idx] else None
            
            # 馬齢・性別分離
            age_sex_match = re.match(r'([牡牝セ])(\d+)', get_field('age_sex') or '')
            if age_sex_match:
                sex = age_sex_match.group(1)
                age = int(age_sex_match.group(2))
            else:
                sex = None
                age = None
            
            # 馬体重パース
            weight, weight_change = self.parse_weight_info(get_field('body_weight') or '')
            
            # 間隔パース
            interval_days = self.parse_interval(get_field('interval') or '')
            
            # 脚質推定
            running_style = self.estimate_running_style(get_field('passing') or '')
            
            # タイム変換
            time_seconds = self.parse_time_to_seconds(get_field('time') or '')
            
            result = {
                'finish_position': self.safe_int(get_field('finish')),
                'gate_number': self.safe_int(get_field('gate')),
                'horse_name': get_field('horse'),
                'age': age,
                'sex': sex,
                'popularity': self.safe_int(get_field('popularity')),
                'jockey_name': get_field('jockey'),
                'jockey_weight': self.safe_float(get_field('jockey_weight')),
                'trainer_name': get_field('trainer'),
                'final_time': get_field('time'),
                'final_time_seconds': time_seconds,
                'last_3f_time': self.safe_float(get_field('last_3f')),
                'weight': weight,
                'weight_change': weight_change,
                'passing_positions': get_field('passing'),
                'estimated_running_style': running_style,
                'sire': get_field('sire'),
                'broodmare_sire': get_field('dam_sire'),
                'previous_race': get_field('prev_race'),
                'days_since_last_race': interval_days,
                'previous_popularity': self.safe_int(get_field('prev_popularity')),
                'previous_finish_position': self.safe_int(get_field('prev_finish'))
            }
            
            return result
            
        except Exception as e:
            self._debug_print(f"結果パースエラー: {e}")
            if self.debug:
                import traceback
                self._debug_print(traceback.format_exc())
            return None
    
    def _parse_statistics(self):
        """統計データ解析"""
        self.current_line += 1
        
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line]
            
            if line.strip() == '枠順':
                self._parse_statistics_table('post_position')
            elif line.strip() == '人気':
                self._parse_statistics_table('popularity')
            elif line.strip() in ['年齢', '所属']:
                self._skip_statistics_table()
            elif line.strip() == '' or self._is_year_header(line):
                break
            
            self.current_line += 1
    
    def _parse_statistics_table(self, category: str):
        """統計テーブル解析"""
        self.current_line += 1
        if self.current_line >= len(self.lines):
            return
        
        header = self.lines[self.current_line]
        if '条件' not in header:
            return
        
        self.current_line += 1
        
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line]
            
            if line.strip() == '' or not '\t' in line:
                break
            
            fields = line.split('\t')
            if len(fields) < 7:
                self.current_line += 1
                continue
            
            try:
                condition = fields[0]
                wins = int(fields[1])
                seconds_val = int(fields[2])
                places_val = int(fields[3])
                win_rate = float(fields[5])
                place_rate = float(fields[6])
                show_rate = float(fields[7])
                
                total_runs = wins + seconds_val + places_val + int(fields[4])
                
                self.statistics[category].append({
                    'condition': condition,
                    'total_runs': total_runs,
                    'wins': wins,
                    'seconds': seconds_val,
                    'places': places_val,
                    'win_rate': win_rate,
                    'place_rate': place_rate,
                    'show_rate': show_rate
                })
            except Exception as e:
                self._debug_print(f"統計データパースエラー: {e}")
            
            self.current_line += 1
    
    def _skip_statistics_table(self):
        """統計テーブルをスキップ"""
        while self.current_line < len(self.lines):
            line = self.lines[self.current_line]
            if line.strip() == '' or (not '\t' in line and not '条件' in line):
                break
            self.current_line += 1


class DatabaseImporter:
    """データベースインポーター"""
    
    def __init__(self, schema: str = SCHEMA_NAME):
        self.schema = schema
        self.conn = psycopg2.connect(DATABASE_URL)
        self.cursor = self.conn.cursor()
        
        # スキーマ設定
        self.cursor.execute(f"SET search_path TO {self.schema}, public")
        print(f"DB接続成功: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'N/A'}")
        print(f"使用スキーマ: {self.schema}")
    
    def import_data(self, parser: KeibaLabTextParser):
        """パース結果をデータベースに投入"""
        print(f"\nデータベースへ投入開始...")
        
        try:
            race_ids = self._import_races(parser.races, parser.race_name, parser.grade)
            self._import_results(parser.race_results, race_ids, parser.races)
            self._import_statistics(parser.race_name, parser.statistics)
            
            # 方針A: 脚質統計はDB格納しない（リアルタイム計算のみ）
            # self._aggregate_running_style_stats(parser.race_name)
            
            self.conn.commit()
            print("✓ データベース投入完了")
            
        except Exception as e:
            print(f"エラー: {e}")
            self.conn.rollback()
            raise
    
    def _import_races(self, races: List[Dict], race_name: str, grade: str) -> Dict[int, int]:
        """レース情報投入"""
        race_ids = {}
        
        for race in races:
            if race.get('date_str') and race.get('year'):
                month, day = map(int, race['date_str'].split('/'))
                race_date = datetime(race['year'], month, day).date()
            else:
                continue
            
            self.cursor.execute(f"""
                INSERT INTO {self.schema}.races 
                (race_name, race_date, race_venue, track_name, distance, 
                 surface, track_condition, weather, grade, race_class, num_horses)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING race_id
            """, (
                race_name,
                race_date,
                race.get('venue'),
                race.get('track_name'),
                race.get('distance'),
                race.get('surface'),
                race.get('track_condition'),
                race.get('weather'),
                grade,
                race.get('race_class'),
                race.get('num_horses')
            ))
            
            race_id = self.cursor.fetchone()[0]
            race_ids[race['year']] = race_id
        
        print(f"  レース情報: {len(race_ids)}件")
        return race_ids
    
    def _import_results(self, results: List[Dict], race_ids: Dict[int, int], races: List[Dict]):
        """レース結果投入"""
        # 各レースの出走頭数を取得
        race_horse_counts = {race['year']: race.get('num_horses', 18) for race in races}
        
        # レース結果を年度ごとにグループ化
        current_year_idx = 0
        years = sorted(race_ids.keys())
        results_count = 0
        
        for i, result in enumerate(results):
            # 現在のレースの想定頭数
            if current_year_idx < len(years):
                year = years[current_year_idx]
                expected_horses = race_horse_counts.get(year, 18)
                
                # 次のレースに移行するかチェック
                if results_count >= expected_horses and current_year_idx + 1 < len(years):
                    current_year_idx += 1
                    year = years[current_year_idx]
                    results_count = 0
                
                race_id = race_ids[year]
                
                self.cursor.execute(f"""
                    INSERT INTO {self.schema}.race_results
                    (race_id, finish_position, gate_number, horse_name, horse_age, horse_sex,
                     popularity, jockey_name, jockey_weight, trainer_name,
                     final_time, final_time_seconds, last_3f_time,
                     weight, weight_change, passing_positions, estimated_running_style,
                     sire, broodmare_sire, previous_race, days_since_last_race,
                     previous_popularity, previous_finish_position)
                    VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    race_id,
                    result['finish_position'],
                    result.get('gate_number'),
                    result['horse_name'],
                    result.get('age'),
                    result.get('sex'),
                    result.get('popularity'),
                    result.get('jockey_name'),
                    result.get('jockey_weight'),
                    result.get('trainer_name'),
                    result.get('final_time'),
                    result.get('final_time_seconds'),
                    result.get('last_3f_time'),
                    result.get('weight'),
                    result.get('weight_change'),
                    result.get('passing_positions'),
                    result.get('estimated_running_style'),
                    result.get('sire'),
                    result.get('broodmare_sire'),
                    result.get('previous_race'),
                    result.get('days_since_last_race'),
                    result.get('previous_popularity'),
                    result.get('previous_finish_position')
                ))
                results_count += 1
        
        print(f"  レース結果: {len(results)}件")
    
    def _import_statistics(self, race_name: str, statistics: Dict):
        """統計データ投入（人気別・枠順別のみ）"""
        count = 0
        
        for category, stats_list in statistics.items():
            for stat in stats_list:
                self.cursor.execute(f"""
                    INSERT INTO {self.schema}.race_statistics
                    (race_name, category, condition, total_runs, wins, seconds, places,
                     win_rate, place_rate, show_rate, years_analyzed)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (race_name, category, condition) 
                    DO UPDATE SET
                        total_runs = EXCLUDED.total_runs,
                        wins = EXCLUDED.wins,
                        seconds = EXCLUDED.seconds,
                        places = EXCLUDED.places,
                        win_rate = EXCLUDED.win_rate,
                        place_rate = EXCLUDED.place_rate,
                        show_rate = EXCLUDED.show_rate,
                        last_updated = CURRENT_TIMESTAMP
                """, (
                    race_name,
                    category,
                    stat['condition'],
                    stat['total_runs'],
                    stat['wins'],
                    stat['seconds'],
                    stat['places'],
                    stat['win_rate'],
                    stat['place_rate'],
                    stat['show_rate'],
                    10
                ))
                count += 1
        
        print(f"  統計データ（人気・枠順）: {count}件")
    
    def verify_data(self, race_name: str):
        """データ確認"""
        print(f"\n=== データ確認: {race_name} ===")
        
        self.cursor.execute(f"SELECT COUNT(*) FROM {self.schema}.races WHERE race_name = %s", (race_name,))
        print(f"レース数: {self.cursor.fetchone()[0]}")
        
        self.cursor.execute(f"""
            SELECT COUNT(*) FROM {self.schema}.race_results rr
            JOIN {self.schema}.races r ON rr.race_id = r.race_id
            WHERE r.race_name = %s
        """, (race_name,))
        result_count = self.cursor.fetchone()[0]
        print(f"レース結果数: {result_count}")
        
        self.cursor.execute(f"SELECT COUNT(*) FROM {self.schema}.race_statistics WHERE race_name = %s", (race_name,))
        print(f"統計データ数（人気・枠順）: {self.cursor.fetchone()[0]}")
        
        # 脚質分布を確認（DB格納していないので動的計算で確認）
        self.cursor.execute(f"""
            SELECT 
                estimated_running_style,
                COUNT(*) as count
            FROM {self.schema}.race_results rr
            JOIN {self.schema}.races r ON rr.race_id = r.race_id
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
        
        print("\n脚質分布（全データ）:")
        for row in self.cursor.fetchall():
            print(f"  {row[0]:4s}: {row[1]:3d}頭")
        
        # 警告: データ数が少ない場合
        if result_count < 100:
            print(f"\n⚠️  注意: レース結果数が少ないため（{result_count}件）、")
            print(f"    脚質統計は参考値としてください。")
            print(f"    完全なデータには各レース15-18頭 × 10年 = 150-180件が必要です。")
    
    def close(self):
        """接続クローズ"""
        self.cursor.close()
        self.conn.close()


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description='競馬ラボテキストデータをパースしてDBに投入（スキーマ分離版）'
    )
    parser.add_argument('--input', required=True, help='入力テキストファイルパス')
    parser.add_argument('--race-name', required=True, help='レース名')
    parser.add_argument('--grade', required=True, help='レースグレード（G1/G2/G3/OP等）')
    parser.add_argument('--schema', default=SCHEMA_NAME, help=f'DBスキーマ名（デフォルト: {SCHEMA_NAME}）')  # 追加
    parser.add_argument('--dry-run', action='store_true', help='パース結果表示のみ（DB投入しない）')
    parser.add_argument('--debug', action='store_true', help='デバッグモード（詳細ログ出力）')
    
    args = parser.parse_args()
    
    print(f"=== 競馬ラボテキストパーサー ===")
    print(f"入力ファイル: {args.input}")
    print(f"レース名: {args.race_name}")
    print(f"グレード: {args.grade}")
    if args.debug:
        print("デバッグモード: ON")
    print()
    
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            text_data = f.read()
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: {args.input}")
        return
    
    text_parser = KeibaLabTextParser(text_data, args.race_name, args.grade, debug=args.debug)
    text_parser.parse()
    
    if args.dry_run:
        print("\n=== ドライラン（DB投入なし）===")
        print(f"パース結果: レース={len(text_parser.races)}件, 結果={len(text_parser.race_results)}件")
        return
    
    db_importer = DatabaseImporter(schema=args.schema)
    try:
        db_importer.import_data(text_parser)
        db_importer.verify_data(args.race_name)
    finally:
        db_importer.close()
    
    print("\n✓ すべての処理が完了しました")


if __name__ == "__main__":
    main()