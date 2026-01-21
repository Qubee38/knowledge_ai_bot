-- 競馬ドメインスキーマ（スキーマ分離対応版）
-- データベース: knowledge_ai_bot
-- スキーマ: horse_racing

-- スキーマ作成
CREATE SCHEMA IF NOT EXISTS horse_racing;

-- 検索パス設定
SET search_path TO horse_racing, public;

-- レース情報
CREATE TABLE IF NOT EXISTS horse_racing.races (
    race_id SERIAL PRIMARY KEY,
    race_name VARCHAR(200) NOT NULL,
    race_date DATE NOT NULL,
    race_venue VARCHAR(100),          -- 開催場所（例: "1回中京5日目"）
    track_name VARCHAR(50),            -- 競馬場（例: "中京", "京都"）
    distance INT,                      -- 距離（例: 1600）
    surface VARCHAR(20),               -- 芝/ダート
    track_condition VARCHAR(20),       -- 馬場状態（良・稍重・重・不良）
    weather VARCHAR(20),               -- 天候
    grade VARCHAR(10),                 -- グレード（G1, G2, G3, OP等）
    race_class VARCHAR(100),           -- レース条件（例: "サラ系3歳オープン"）
    num_horses INT,                    -- 出走頭数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- レース結果（詳細）
CREATE TABLE IF NOT EXISTS horse_racing.race_results (
    result_id SERIAL PRIMARY KEY,
    race_id INT REFERENCES horse_racing.races(race_id) ON DELETE CASCADE,
    
    -- 基本情報
    finish_position INT NOT NULL,      -- 着順
    gate_number INT,                   -- 枠番（1-8）
    horse_name VARCHAR(100) NOT NULL,
    horse_age INT,                     -- 馬齢
    horse_sex VARCHAR(10),             -- 性別（牡・牝・セン）
    
    -- 人気・オッズ
    popularity INT,                    -- 人気順
    
    -- 騎手・調教師
    jockey_name VARCHAR(100),
    jockey_weight DECIMAL(4,1),        -- 斤量
    trainer_name VARCHAR(100),         -- 厩舎
    
    -- タイム・着差
    final_time VARCHAR(20),            -- タイム（例: "1:34.6"）
    final_time_seconds DECIMAL(6,2),   -- タイム（秒換算）
    margin VARCHAR(20),                -- 着差
    last_3f_time DECIMAL(4,1),         -- 上がり3ハロン
    
    -- 馬体重
    weight INT,                        -- 馬体重
    weight_change INT,                 -- 馬体重増減
    
    -- 通過順位・脚質
    passing_positions VARCHAR(50),     -- 通過順位（例: "－④⑧⑨"）
    estimated_running_style VARCHAR(20), -- 推定脚質（逃げ/先行/差し/追込）
    
    -- 血統
    sire VARCHAR(100),                 -- 父
    broodmare_sire VARCHAR(100),       -- 母父
    
    -- 前走情報
    previous_race VARCHAR(100),        -- 前走レース名
    days_since_last_race INT,          -- 前走からの間隔（週）
    previous_popularity INT,           -- 前走人気
    previous_finish_position INT,      -- 前走着順
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 集計済み統計データ（確定版）
CREATE TABLE IF NOT EXISTS horse_racing.race_statistics (
    stat_id SERIAL PRIMARY KEY,
    race_name VARCHAR(200) NOT NULL,
    
    -- 集計カテゴリ
    category VARCHAR(50) NOT NULL,     -- popularity, post_position, running_style等
    condition VARCHAR(100) NOT NULL,   -- 具体的な条件（例: "1番人気", "逃げ", "1枠"）
    
    -- 集計結果
    races_count INT,                   -- 対象レース数
    total_runs INT,                    -- 総出走数
    wins INT,                          -- 1着回数
    seconds INT,                       -- 2着回数
    places INT,                        -- 3着回数（2着を含まない）
    
    -- 勝率・連対率・複勝率
    win_rate DECIMAL(5,2),             -- 勝率（%）
    place_rate DECIMAL(5,2),           -- 連対率（%）2着まで
    show_rate DECIMAL(5,2),            -- 複勝率（%）3着まで
    
    -- 回収率（将来的に追加）
    win_payback DECIMAL(10,2),
    place_payback DECIMAL(10,2),
    
    -- メタ情報
    years_analyzed INT,                -- 集計対象年数
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(race_name, category, condition)
);

-- 消去法統計
CREATE TABLE IF NOT EXISTS horse_racing.elimination_statistics (
    elim_stat_id SERIAL PRIMARY KEY,
    race_name VARCHAR(200) NOT NULL,
    
    -- 条件タイプ
    condition_type VARCHAR(50) NOT NULL,
    condition_value VARCHAR(100) NOT NULL,
    
    -- 集計結果
    sample_size INT,
    wins INT,
    seconds INT,
    places INT,
    win_rate DECIMAL(5,2),
    place_rate DECIMAL(5,2),
    show_rate DECIMAL(5,2),
    
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(race_name, condition_type, condition_value)
);

-- インデックス作成
CREATE INDEX idx_hr_races_name_date ON horse_racing.races(race_name, race_date);
CREATE INDEX idx_hr_races_date ON horse_racing.races(race_date);
CREATE INDEX idx_hr_races_grade ON horse_racing.races(grade);
CREATE INDEX idx_hr_results_race ON horse_racing.race_results(race_id);
CREATE INDEX idx_hr_results_finish ON horse_racing.race_results(finish_position);
CREATE INDEX idx_hr_results_popularity ON horse_racing.race_results(popularity);
CREATE INDEX idx_hr_results_style ON horse_racing.race_results(estimated_running_style);
CREATE INDEX idx_hr_statistics_race_category ON horse_racing.race_statistics(race_name, category);
CREATE INDEX idx_hr_elimination_race_type ON horse_racing.elimination_statistics(race_name, condition_type);

-- ビュー: レース結果と統計の結合（便利用）
CREATE OR REPLACE VIEW horse_racing.race_results_with_stats AS
SELECT 
    r.race_name,
    r.race_date,
    r.track_name,
    r.grade,
    r.distance,
    rr.finish_position,
    rr.horse_name,
    rr.popularity,
    rr.jockey_name,
    rr.last_3f_time,
    rr.estimated_running_style
FROM horse_racing.races r
JOIN horse_racing.race_results rr ON r.race_id = rr.race_id;

-- 確認
SELECT 'スキーマ作成完了: horse_racing' as status;