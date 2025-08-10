import React from "react";
import { BaseEdge, EdgeLabelRenderer, getBezierPath } from "@xyflow/react";

type SmartEdgeProps = React.ComponentProps<typeof BaseEdge> & {
  label?: string;
};

const SmartEdge: React.FC<SmartEdgeProps> = (props) => {
  const [edgePath, labelX, labelY] = getBezierPath(props);

  return (
    <>
      <BaseEdge path={edgePath} {...props} />
      {props.label ? (
        <EdgeLabelRenderer>
          <div
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: "all",
            }}
            className="rounded bg-background px-1 py-0.5 text-xs shadow"
          >
            {props.label}
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  );
};

export default SmartEdge;
