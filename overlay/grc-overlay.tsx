import { Card } from "@/components/opal/Card";
import { ControlCoverageChart } from "@/components/grc/ControlCoverageChart";
import type { ProductOverlay } from "./types";

/**
 * mynd ComplianceVault overlay.
 *
 * Adds a SOC2 control-coverage widget to the dashboard. Everything else
 * (branding, layout, chat, connectors) comes from the shared design system and
 * config/grc.
 */
export const grcOverlay: ProductOverlay = {
  extendDashboard(slug: string) {
    if (slug !== "grc") return [];
    return [
      <Card key="grc-control-coverage" title="SOC2 Control Coverage">
        <ControlCoverageChart />
      </Card>,
    ];
  },
};

export default grcOverlay;
