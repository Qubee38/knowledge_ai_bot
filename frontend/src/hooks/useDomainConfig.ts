import { useState, useEffect } from 'react';
import { DomainConfig } from '../types';

export const useDomainConfig = () => {
  const [domainConfig, setDomainConfig] = useState<DomainConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        setLoading(true);
        
        const response = await fetch('/api/config/domain');
        
        if (!response.ok) {
          throw new Error(`Failed to fetch domain config: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Domain config loaded:', data);
        
        setDomainConfig(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching domain config:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();
  }, []);

  return { domainConfig, loading, error };
};