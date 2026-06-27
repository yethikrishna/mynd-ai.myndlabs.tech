"use client";

import React from "react";
import Button from "@/refresh-components/buttons/Button";
import Text from "@/refresh-components/texts/Text";
import { useProduct } from "../ProductContext";
import { useProductAgents, useProductCapabilities } from "../hooks";

/**
 * Product-branded sidebar for the app shell. Surfaces the product's enabled
 * agents (seeded as Onyx personas) and connectors from config, and gates admin
 * actions (connectors, model settings) by the user's resolved capabilities.
 *
 * Agents link into Onyx's real chat experience (`/app`) with the seeded persona
 * preselected by name; product context travels via the `mynd_product` cookie.
 */
export function ProductSidebar() {
  const { slug, config } = useProduct();
  const { agents } = useProductAgents(slug);
  const { has } = useProductCapabilities(slug);

  if (!slug || !config) return null;

  return (
    <aside className="flex h-full w-64 flex-col gap-4 border-r border-border-01 p-4">
      <div className="flex items-center gap-2">
        <span
          className="h-3 w-3 rounded-full"
          style={{ background: "var(--mynd-primary)" }}
        />
        <Text mainUiAction text01>
          {config.name}
        </Text>
      </div>

      <section className="flex flex-col gap-1">
        <Text text03 secondaryBody>
          Agents
        </Text>
        {agents.length === 0 ? (
          <Text text03 secondaryBody>
            No agents configured.
          </Text>
        ) : (
          agents.map((a) => (
            <Button
              key={a.key}
              action
              tertiary
              size="md"
              href={`/app?agent=${encodeURIComponent(a.persona_name)}`}
              title={a.description}
            >
              {a.name}
            </Button>
          ))
        )}
      </section>

      <section className="flex flex-col gap-1">
        <Text text03 secondaryBody>
          Connectors
        </Text>
        {config.enabled_connectors.map((c) => (
          <Text key={c} text02 mainUiBody>
            {c}
          </Text>
        ))}
      </section>

      <div className="mt-auto flex flex-col gap-1">
        {has("manage_connectors") && (
          <Button action tertiary size="md" href="/admin/connectors">
            Manage connectors
          </Button>
        )}
        <Button
          action
          tertiary
          size="md"
          href={`/${slug}/settings/models`}
        >
          Model settings
        </Button>
        {has("view_audit_logs") && (
          <Text text03 secondaryBody>
            Audit: enabled
          </Text>
        )}
      </div>
    </aside>
  );
}

export default ProductSidebar;
