"use client";

import React, { createContext, useContext } from "react";
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
