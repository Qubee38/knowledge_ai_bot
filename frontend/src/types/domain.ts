/**
 * ドメイン関連の型定義
 */

export interface DomainInfo {
  domain_id: string;
  name: string;
  description: string;
  access_status: 'active' | 'pending' | null;
  requested_at: string | null;
  approved_at: string | null;
}

export interface DomainAccessRequest {
  reason?: string;
}

export interface DomainAccessResponse {
  access_id: string;
  domain_id: string;
  status: string;
  requested_at: string;
  approved_at: string | null;
}