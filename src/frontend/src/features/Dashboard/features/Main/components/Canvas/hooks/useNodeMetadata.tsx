import { useMemo } from "react";
import type { NodeMetadata } from "../components/EnhancedNode";
import type { BaseNode } from "@/types/project";

/**
 * Lightweight metadata hook – no network calls, just enriches with provided data.
 * Keeps room to extend later (logs, runtime stats, etc.).
 */
export const useNodeMetadata = (
  node: BaseNode | null,
  code?: string,
  description?: string
): NodeMetadata => {
  return useMemo(
    () => ({
      createdAt: node?.created_at,
      updatedAt: node?.updated_at,
      code,
      fileName: node?.name,
      description,
      status: "idle",
    }),
    [code, description, node?.created_at, node?.name, node?.updated_at]
  );
};
