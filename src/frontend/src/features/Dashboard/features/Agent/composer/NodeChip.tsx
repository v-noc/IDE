import { NodeRefChip } from "../thread/parts/NodeRefChip";
import type { NodeRefPart } from "../stream/types";

interface NodeChipProps {
  part: NodeRefPart;
  onFocus?: (part: NodeRefPart) => void;
  onRemove?: () => void;
}

export function NodeChip({ part, onFocus, onRemove }: NodeChipProps) {
  return <NodeRefChip part={part} onFocus={onFocus} onRemove={onRemove} />;
}
