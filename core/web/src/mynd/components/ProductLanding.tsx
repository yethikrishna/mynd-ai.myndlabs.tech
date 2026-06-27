"use client";

import React from "react";
import Button from "@/refresh-components/buttons/Button";
import Text from "@/refresh-components/texts/Text";
import { Card } from "@/refresh-components/cards";
import { useProduct } from "../ProductContext";
import { getOverlay } from "../overlays";

/**
 * Per-product marketing/landing page, composed entirely from the shared design
 * system and driven by config/<slug> (branding, tagline, connectors, features).
 * Only content + accent color change per product — layout/components are shared.
 */
export function ProductLanding() {
  const { slug, config, isLoading, error } = useProduct();

  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center p-8">
        <Text text03 mainUiBody>
          Loading…
        </Text>
      </div>
    );
  }

  if (error || !config || !slug) {
    return (
      <div className="flex h-full w-full items-center justify-center p-8">
        <Text text03 mainUiBody>
          Product not found.
        </Text>
      </div>
    );
  }

  const overlayWidgets = getOverlay(slug).extendDashboard?.(slug) ?? [];
  const features = Object.entries(config.features).filter(([, on]) => on);

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-8 p-8">
      {/* Hero */}
      <section className="flex flex-col gap-3">
        <span
          className="inline-block w-fit rounded-full px-3 py-1 text-sm font-medium text-white"
          style={{ background: "var(--mynd-primary)" }}
        >
          {config.name}
        </span>
        <Text headingH1>{config.branding.marketing_tagline}</Text>
        <Text text03 mainUiBody>
          {config.description}
        </Text>
        <div className="mt-2 flex gap-2">
          <Button main primary href={`/${slug}/app`}>
            Open {config.name}
          </Button>
          <Button action secondary href={`/${slug}/settings/models`}>
            Model settings
          </Button>
        </div>
      </section>

      {/* Features */}
      {features.length > 0 && (
        <section className="flex flex-col gap-3">
          <Text headingH3>Capabilities</Text>
          <div className="flex flex-wrap gap-2">
            {features.map(([name]) => (
              <span
                key={name}
                className="rounded-08 border border-border-01 px-3 py-1 text-sm"
              >
                {name.replace(/_/g, " ")}
              </span>
            ))}
          </div>
        </section>
      )}

      {/* Connectors */}
      {config.enabled_connectors.length > 0 && (
        <section className="flex flex-col gap-3">
          <Text headingH3>Connects to</Text>
          <div className="flex flex-wrap gap-2">
            {config.enabled_connectors.map((c) => (
              <Card key={c} variant="secondary">
                <Text text02 mainUiBody>
                  {c}
                </Text>
              </Card>
            ))}
          </div>
        </section>
      )}

      {/* Overlay-contributed widgets (e.g. GRC control coverage) */}
      {overlayWidgets.length > 0 && (
        <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {overlayWidgets}
        </section>
      )}
    </div>
  );
}

export default ProductLanding;
