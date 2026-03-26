import type { Walkthrough } from "@/features/Dashboard/features/Agent/walkthrough/types/walkthrough";

export interface WalkthroughWirePart {
  type: "walkthrough";
  /** Optional stable id for analytics / future hydration */
  tour_id?: string;
  title: string;
  description?: string;
  icon?: string;
  workflow_name?: string;
  walkthrough: Walkthrough;
}
