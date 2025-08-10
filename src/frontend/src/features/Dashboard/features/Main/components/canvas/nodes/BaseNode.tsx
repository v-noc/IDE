import React, { useCallback, useEffect, useRef } from "react";
import { Position, useReactFlow } from "@xyflow/react";
import CustomHandle from "./CustomHandle";
import { DynamicIcon } from "@/components/DynamicIcon";
import { cn } from "@/lib/utils";
import useProjectStore from "@/features/Dashboard/store/useProjectStore";

type BaseNodeTheme = {
  iconColor?: string;
  cardColor?: string;
  textColor?: string;
};

interface BaseNodeProps extends React.ComponentProps<"div"> {
  id: string;
  iconName?: string;
  title: string;
  theme?: BaseNodeTheme;
  headerRight?: React.ReactNode;
  showHandles?: boolean;
  isSelected: boolean;
}

const BaseNode: React.FC<BaseNodeProps> = ({
  id,
  iconName,
  title,
  theme,
  headerRight,
  showHandles = true,
  className = "",
  isSelected,
  children,
  ...rest
}) => {
  const { setSelectedNodeId } = useProjectStore();

  const rf = useReactFlow();
  const nodeRef = useRef<HTMLDivElement | null>(null);
  const hasCentered = useRef(false);

  const centerNode = useCallback(() => {
    const node = rf.getNode(id);
    const x = node?.position?.x ?? 0;
    const y = node?.position?.y ?? 0;
    const width = node?.width ?? nodeRef.current?.offsetWidth ?? 300;
    const height = node?.height ?? nodeRef.current?.offsetHeight ?? 160;
    rf.setCenter(x + width / 2, y + height / 2, { zoom: 1.2, duration: 400 });
  }, [rf, id]);

  const handleDoubleClick = () => {
    centerNode();
  };

  useEffect(() => {
    console.log("isSelected", isSelected, " ", hasCentered);
    if (isSelected) {
      // wait a tick so layout has widths/heights
      setTimeout(() => {
        requestAnimationFrame(() => centerNode());
      }, 100);
    }
  }, [isSelected, id, centerNode]);
  return (
    <div
      ref={nodeRef}
      {...rest}
      className={cn(
        "w-[300px] rounded-xl bg-card text-card-foreground shadow border",
        isSelected ? "ring-2 ring-primary border-primary" : "",
        className
      )}
      style={{
        ...(rest.style as React.CSSProperties),
        ...(theme?.cardColor ? { backgroundColor: theme.cardColor } : {}),
      }}
      onClick={() => setSelectedNodeId(id)}
      onDoubleClick={handleDoubleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          setSelectedNodeId(id);
        }
      }}
    >
      <div className="border-b px-4 py-3 text-base font-semibold flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {iconName ? (
            <DynamicIcon
              iconName={iconName}
              className={cn("h-4 w-4 flex-shrink-0")}
              color={theme?.iconColor}
            />
          ) : null}
          <span
            className={cn("text-sm truncate")}
            title={title}
            style={theme?.textColor ? { color: theme.textColor } : undefined}
          >
            {title}
          </span>
        </div>
        {headerRight}
      </div>
      <div className="px-4 py-3">{children}</div>
      {showHandles ? (
        <>
          <CustomHandle type="target" position={Position.Left} size={16} />
          <CustomHandle type="source" position={Position.Right} size={16} />
        </>
      ) : null}
    </div>
  );
};

export default BaseNode;
