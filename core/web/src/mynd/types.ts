// Shared types for the mynd product layer (frontend mirror of
// core/backend/mynd/platform_config and the llm-credentials API).

export interface ProductBranding {
  primary_color: string;
  logo: string;
  marketing_tagline: string;
}

export interface ProductConfig {
  slug: string;
  name: string;
  description: string;
  branding: ProductBranding;
  enabled_connectors: string[];
  default_llm_providers: string[];
  features: Record<string, boolean>;
}

export interface ProviderMeta {
  name: string;
  supports_base_url: boolean;
  supports_oauth: boolean;
}

export type CredentialScope = "user" | "org";

export interface CredentialSummary {
  id: string;
  provider_name: string;
  credential_type: string;
  base_url: string | null;
  is_default: boolean;
}

export interface UpsertCredentialBody {
  provider_name: string;
  credential_type?: string;
  api_key?: string;
  base_url?: string;
  is_default?: boolean;
}
