import React from "react";
import { ProductProvider } from "@/mynd/ProductContext";

/**
 * Product route group: ai.myndlabs.tech/<productSlug>/...
 *
 * Static Onyx routes (/admin, /chat, /app, …) take precedence over this dynamic
 * segment, so only product slugs (eng, grc, sales, …) and unknown first
 * segments land here. The ProductProvider fetches config/<slug> and applies
 * per-product branding to the subtree.
 */
export default async function ProductLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ productSlug: string }>;
}) {
  const { productSlug } = await params;
  return <ProductProvider slug={productSlug}>{children}</ProductProvider>;
}
