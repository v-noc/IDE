import React from "react";

interface LabeledRectProps {
    ariaLabel?: string;
    backgroundColor: string;
    color: string;
    height: number;
    isDimmed?: boolean;
    label: string;
    onActivate?: () => void;
    onMouseEnter?: (e: React.MouseEvent) => void;
    onMouseLeave?: (e: React.MouseEvent) => void;
    onMouseMove?: (e: React.MouseEvent) => void;
    width: number;
    x: number;
    y: number;
}

const MIN_WIDTH_TO_DISPLAY_TEXT = 30; // 30px
const TEXT_HEIGHT = 14; // Approximate

export const LabeledRect: React.FC<LabeledRectProps> = ({
    ariaLabel,
    backgroundColor,
    color,
    height,
    isDimmed = false,
    label,
    onActivate,
    onMouseEnter,
    onMouseLeave,
    onMouseMove,
    width,
    x,
    y,
}) => (
    <g
        className="transition-opacity duration-200"
        transform={`translate(${x},${y})`}
        onMouseEnter={onMouseEnter}
        onMouseLeave={onMouseLeave}
        onMouseMove={onMouseMove}
    >
        <rect
            width={width}
            height={height}
            fill={backgroundColor || "#3b82f6"}
            onClick={onActivate}
            onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    onActivate?.();
                }
            }}
            role="button"
            tabIndex={0}
            aria-label={ariaLabel || label}
            className="cursor-pointer stroke-white/30 hover:brightness-95 transition-all outline-none focus-visible:stroke-blue-500 focus-visible:stroke-2"
            style={{
                opacity: isDimmed ? 0.5 : 1,
            }}
        />
        {width >= MIN_WIDTH_TO_DISPLAY_TEXT && (
            <foreignObject
                width={width}
                height={height}
                className="pointer-events-none overflow-hidden"
                style={{
                    opacity: isDimmed ? 0.75 : 1,
                    paddingLeft: x < 0 ? -x : 0,
                }}
                y={height < TEXT_HEIGHT ? -TEXT_HEIGHT : 0}
            >
                <div
                    className="truncate px-1 text-[10px] font-sans h-full flex items-center justify-center leading-none"
                    style={{ color }}
                >
                    {label}
                </div>
            </foreignObject>
        )}
    </g>
);
