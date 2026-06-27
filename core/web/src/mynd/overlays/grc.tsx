import React from "react";
import { Card } from "@/refresh-components/cards";
import Text from "@/refresh-components/texts/Text";
import type { ProductOverlay } from "./index";

/**
 * mynd ComplianceVault overlay — adds a SOC2 control-coverage widget.
 *
 * Placeholder chart kept dependency-free; swap the body for a real
 * `@/components/grc/ControlCoverageChart` once that component exists.
 */
function ControlCoverageChart() {
  const controls = [
    { name: "Access Control", pct: 92 },
    { name: "Change Mgmt", pct: 78 },
    { name: "Monitoring", pct: 64 },
  ];
  return (
    <div className="flex flex-col gap-2">
      {controls.map((c) => (
        <div key={c.name} className="flex flex-col gap-1">
          <Text text03 secondaryBody>
            {c.name} — {c.pct}%
          </Text>
          <div className="h-2 w-full rounded-full bg-background-tint-02">
            <div
              className="h-2 rounded-full"
              style={{ width: `${c.pct}%`, background: "var(--mynd-primary)" }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export const grcOverlay: ProductOverlay = {
  extendDashboard(slug: string) {
    if (slug !== "grc") return [];
    return [
      <Card key="grc-control-coverage">
        <Text headingH3>SOC2 Control Coverage</Text>
        <ControlCoverageChart />
      </Card>,
    ];
  },
};

export default grcOverlay;
