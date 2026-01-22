/**
 * ドメイン管理サービス
 */
import apiClient from './api';
import { API_ENDPOINTS } from '../utils/constants';
import { DomainInfo, DomainAccessRequest, DomainAccessResponse } from '../types/domain';

export const domainsService = {
  /**
   * ドメイン一覧取得
   */
  async getDomains(): Promise<DomainInfo[]> {
    const response = await apiClient.get<DomainInfo[]>(API_ENDPOINTS.DOMAINS);
    return response.data;
  },

  /**
   * ドメインアクセス申請
   */
  async requestDomainAccess(
    domainId: string,
    data: DomainAccessRequest
  ): Promise<DomainAccessResponse> {
    const response = await apiClient.post<DomainAccessResponse>(
      API_ENDPOINTS.DOMAIN_REQUEST(domainId),
      data
    );
    return response.data;
  },

  /**
   * ドメインアクセス取り消し
   */
  async revokeDomainAccess(domainId: string): Promise<void> {
    await apiClient.delete(API_ENDPOINTS.DOMAIN_REVOKE(domainId));
  },

  /**
   * ドメインアクセス権確認
   */
  async checkDomainAccess(domainId: string): Promise<{ has_access: boolean; status: string | null }> {
    const response = await apiClient.get(API_ENDPOINTS.DOMAIN_CHECK(domainId));
    return response.data;
  },
};