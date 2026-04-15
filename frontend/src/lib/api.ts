import axios from 'axios';

const BACKEND_ADDRESS_STORAGE_KEY = 'rd_backend_address';
const DEFAULT_API_BASE_URL = 'http://localhost:8000/api';

function buildApiBaseUrl(address: string) {
  const trimmed = address.trim();
  if (!trimmed) throw new Error('Backend address is required.');

  const withProtocol = /^https?:\/\//i.test(trimmed) ? trimmed : `http://${trimmed}`;
  const withoutTrailingSlash = withProtocol.replace(/\/+$/, '');
  return withoutTrailingSlash.endsWith('/api') ? withoutTrailingSlash : `${withoutTrailingSlash}/api`;
}

function getStoredApiBaseUrl() {
  if (typeof window === 'undefined') return DEFAULT_API_BASE_URL;
  const stored = window.localStorage.getItem(BACKEND_ADDRESS_STORAGE_KEY);
  if (!stored) return DEFAULT_API_BASE_URL;
  try {
    return buildApiBaseUrl(stored);
  } catch {
    return DEFAULT_API_BASE_URL;
  }
}

export const api = axios.create({ baseURL: getStoredApiBaseUrl() });

export function getBackendAddress() {
  const baseUrl = api.defaults.baseURL ?? DEFAULT_API_BASE_URL;
  return baseUrl.endsWith('/api') ? baseUrl.slice(0, -4) : baseUrl;
}

export function setBackendAddress(address: string) {
  const nextBaseUrl = buildApiBaseUrl(address);
  api.defaults.baseURL = nextBaseUrl;
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(BACKEND_ADDRESS_STORAGE_KEY, getBackendAddress());
  }
  return nextBaseUrl;
}

export async function testBackendConnection(address: string) {
  const client = axios.create({ baseURL: buildApiBaseUrl(address), timeout: 5000 });
  await client.get('/health');
}
