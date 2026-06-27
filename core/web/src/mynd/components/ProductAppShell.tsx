"use client";

import React from "react";
import Button from "@/refresh-components/buttons/Button";
import Text from "@/refresh-components/texts/Text";
import { Card } from "@/refresh-components/cards";
import { useProduct } from "../ProductContext";
import { useProductAgents } from "../hooks";
import ProductSidebar from "./ProductSidebar";

/**
 * Product app shell at ai.myndlabs.tech/<slug>/app.
 *
 * Composes a product-branded chrome (sidebar from config: agents + connectors,
 * capability-gated admin actions) around an entry panel into Onyx's real chat.
 * The shell intentionally does NOT re-mount Onyx's full chat client (which owns
 * its own provider tree); instead it launches Onyx chat with the product's
 * seeded agents, while the `mynd_product` cookie (set by ProductProvider)
 * carries product context to every Onyx API call so BYO credentials and audit
 * apply.
 */
export function ProductAppShell() {
  const { slug, config, isLoading } = useProduct();
  const { agents } = useProductAgents(slug);

  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center p-8">
        <Text text03 mainUiBody>
          Loading…
        </Text>
      </div>
    );
  }
  if (!slug || !config) {
    return (
      <div className="flex h-full w-full items-center justify-center p-8">
        <Text text03 mainUiBody>
          Product not found.
        </Text>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full">
      <ProductSidebar />
      <main className="flex flex-1 flex-col gap-6 p-8">
        <div className="flex flex-col gap-2">
          <Text headingH1>{config.name}</Text>
          <Text text03 mainUiBody>
            {config.description}
          </Text>
          <div className="flex gap-2">
            <Button main primary href="/app">
              Start a chat
            </Button>
          </div>
        </div>

        {agents.length > 0 && (
          <section className="flex flex-col gap-3">
            <Text headingH3>Start with an agent</Text>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              {agents.map((a) => (
                <Card key={a.key}>
                  <Text mainUiAction text01>
                    {a.name}
                  </Text>
                  <Text text03 secondaryBody>
                    {a.description}
                  </Text>
                  <Button
                    action
                    secondary
                    href={`/app?agent=${encodeURIComponent(a.persona_name)}`}
                  >
                    Use {a.name}
                  </Button>
                </Card>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

export default ProductAppShell;
