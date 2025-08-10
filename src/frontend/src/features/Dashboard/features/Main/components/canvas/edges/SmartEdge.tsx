import React from "react";
import {
  BaseEdge,
  EdgeLabelRenderer,
  getBezierPath,
  type EdgeProps,
} from "@xyflow/react";

interface SmartEdgeProps extends EdgeProps {
  label?: string;
}

const SmartEdge: React.FC<SmartEdgeProps> = (props) => {
  const { id, markerEnd, markerStart, label } = props;
  const [edgePath, labelX, labelY] = getBezierPath(props);

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        markerStart={markerStart}
        style={{
          strokeWidth: 3,
        }}
      />
      {label ? (
        <EdgeLabelRenderer>
          <div
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: "all",
            }}
            className="rounded bg-background px-1 py-0.5 text-xs shadow"
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      ) : null}
    </>
  );
};

export default SmartEdge;
