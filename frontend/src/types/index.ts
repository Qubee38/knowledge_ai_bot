// メッセージ型
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// ドメイン設定型
export interface DomainConfig {
  domain: {
    id: string;
    name: string;
    description: string;
    version: string;
  };
  ui: {
    theme: {
      primary: string;
      secondary: string;
      accent: string;
    };
    quick_actions: QuickAction[];
    sample_queries: string[];
  };
}

export interface QuickAction {
  label: string;
  query: string;
  icon: string;
}

// 統計データ型
export interface StatisticsData {
  race_name: string;
  category: string;
  data: StatRow[];
  years_analyzed: number;
  data_quality?: string;
  note?: string;
  warning?: string;
  total_sample?: number;
}

export interface StatRow {
  condition: string;
  total_runs?: number;
  wins: number;
  seconds?: number;
  places?: number;
  top3?: number;
  win_rate: number;
  place_rate?: number;
  show_rate?: number;
  sample_size: number;
}

// エラー型
export interface ErrorResponse {
  error: string;
  race_name?: string;
  category?: string;
}

// ユーザー管理機能の新規追加
export * from './auth';
export * from './domain';