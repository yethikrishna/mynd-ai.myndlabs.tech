// API client for the mynd product layer. Reuses Onyx's session cookie auth
// (credentials: "include" is implicit for same-origin) and its error fetcher.

import { errorHandlingFetcher } from "@/lib/fetcher";
import type {
  CredentialScope,
  CredentialSummary,
  ProductConfig,
  ProviderMeta,
  UpsertCredentialBody,
} from "./types";

// --- product config -------------------------------------------------------
export const productConfigKey = (slug: string) => `/api/config/${slug}`;

export const fetchProductConfig = (slug: string): Promise<ProductConfig> =>
  errorHandlingFetcher<ProductConfig>(productConfigKey(slug));

export const fetchProductSlugs = (): Promise<{ products: string[] }> =>
  errorHandlingFetcher<{ products: string[] }>("/api/config");

// --- llm credentials ------------------------------------------------------
export const providersKey = "/api/llm-credentials/providers";

export const fetchProviders = (): Promise<{ providers: ProviderMeta[] }> =>
  errorHandlingFetcher<{ providers: ProviderMeta[] }>(providersKey);

export const credentialsKey = (scope: CredentialScope) =>
  `/api/llm-credentials/${scope}`;

export const fetchCredentials = (
  scope: CredentialScope
): Promise<CredentialSummary[]> =>
  errorHandlingFetcher<CredentialSummary[]>(credentialsKey(scope));

async function jsonOrThrow(res: Response) {
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(detail || `Request failed (${res.status})`);
  }
  return res.status === 204 ? null : res.json();
}

export const upsertCredential = (
  scope: CredentialScope,
  body: UpsertCredentialBody
) =>
  fetch(credentialsKey(scope), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }).then(jsonOrThrow);

export const deleteCredential = (scope: CredentialScope, id: string) =>
  fetch(`${credentialsKey(scope)}/${id}`, { method: "DELETE" }).then(
    jsonOrThrow
  );

export const startOAuth = (provider: string): Promise<{ authorize_url: string }> =>
  errorHandlingFetcher<{ authorize_url: string }>(
    `/api/llm-credentials/oauth/${provider}/start`
  );
