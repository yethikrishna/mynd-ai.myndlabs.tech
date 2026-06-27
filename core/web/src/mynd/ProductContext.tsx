"use client";

import React, { createContext, useContext, useEffect } from "react";
import useSWR from "swr";
import { errorHandlingFetcher } from "@/lib/fetcher";
import { productConfigKey } from "./api";
import type { ProductConfig } from "./types";

interface ProductContextValue {
  slug: string | null;
  config: ProductConfig | null;
  isLoading: boolean;
  error: unknown;
}

const ProductContext = createContext<ProductContextValue>({
  slug: null,
  config: null,
  isLoading: false,
  error: null,
});

/**
 * Provides the active product's config (branding, features, connectors) to the
 * subtree and applies its primary color as a CSS variable (`--mynd-primary`)
 * so product surfaces can theme without touching the shared design system.
 */
export function ProductProvider({
  slug,
  children,
}: {
  slug: string | null;
  children: React.ReactNode;
}) {
  const { data, error, isLoading } = useSWR<ProductConfig>(
    slug ? productConfigKey(slug) : null,
    errorHandlingFetcher
  );

  // Carry product context to ALL subsequent API calls (including Onyx's own
  // chat/connector requests, which are not under /<slug>) via a cookie the
  // backend middleware reads. This is what makes BYO-credential resolution and
  // per-product audit fire for the chat experience.
  useEffect(() => {
    if (typeof document === "undefined" || !slug) return;
    document.cookie = `mynd_product=${slug}; path=/; SameSite=Lax`;
  }, [slug]);

  const config = data ?? null;
  const style = config
    ? ({ ["--mynd-primary" as string]: config.branding.primary_color } as React.CSSProperties)
    : undefined;

  return (
    <ProductContext.Provider value={{ slug, config, isLoading, error }}>
      <div data-product={slug ?? undefined} style={style}>
        {children}
      </div>
    </ProductContext.Provider>
  );
}

export function useProduct(): ProductContextValue {
  return useContext(ProductContext);
}
