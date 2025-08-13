import React from "react";
import { Handle, type Position } from "@xyflow/react";

type CustomHandleProps = React.ComponentProps<typeof Handle> & {
  size?: number;
  className?: string;
  position: Position;
};

const CustomHandle: React.FC<CustomHandleProps> = ({
  size = 20,
  className = "",
  style,
  ...props
}) => {
  return (
    <Handle
      {...props}
      className={`rounded-full border-2 border-primary bg-primary ${className}`}
      style={{ width: size, height: size, ...style }}
    />
  );
};

export default CustomHandle;
