/**
 * ドメイン管理サービス
 */
import api from './api';
import {
  DomainInfo,
  DomainAccessRequest,
  DomainAccessResponse,
  DomainsResponse,  // ← 追加
} from '../types/domain';

export const domainsService = {
  /**
   * ドメイン一覧取得
   */
  async getDomains(): Promise<DomainsResponse> {  // ← 戻り値の型を修正
    const response = await api.get<DomainsResponse>('/api/domains');
    return response.data;
  },

  /**
   * ドメインアクセス申請
   */
  async requestDomainAccess(
    domainId: string,
    data: DomainAccessRequest
  ): Promise<DomainAccessResponse> {
    const response = await api.post<DomainAccessResponse>(
      `/api/domains/${domainId}/request`,
      data
    );
    return response.data;
  },

  /**
   * ドメインアクセス取り消し
   */
  async revokeDomainAccess(domainId: string): Promise<void> {
    await api.delete(`/api/domains/${domainId}/access`);
  },

  /**
   * ドメインアクセス権確認
   */
  async checkDomainAccess(domainId: string): Promise<{
    has_access: boolean;
    status: string | null;
  }> {
    const response = await api.get(
      `/api/domains/check-access/${domainId}`
    );
    return response.data;
  },
};