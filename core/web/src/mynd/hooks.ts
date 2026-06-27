"use client";

import useSWR from "swr";
import { errorHandlingFetcher } from "@/lib/fetcher";
import {
  capabilitiesKey,
  productAgentsKey,
  type Capabilities,
  type ProductAgent,
} from "./api";

export function useProductAgents(slug: string | null) {
  const { data, error, isLoading } = useSWR<{ agents: ProductAgent[] }>(
    slug ? productAgentsKey(slug) : null,
    errorHandlingFetcher
  );
  return { agents: data?.agents ?? [], error, isLoading };
}

export function useProductCapabilities(slug: string | null) {
  const { data, error, isLoading } = useSWR<Capabilities>(
    slug ? capabilitiesKey(slug) : null,
    errorHandlingFetcher
  );
  const has = (cap: string) => Boolean(data?.capabilities.includes(cap));
  return { capabilities: data?.capabilities ?? [], has, error, isLoading };
}
