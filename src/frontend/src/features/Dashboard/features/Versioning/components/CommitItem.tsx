import React from "react";
import { GitCommit, GitCompare, History } from "lucide-react";
import type { CommitDisplay } from "../store/useVersioningStore";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuItem,
  ContextMenuSeparator,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";

interface CommitItemProps {
  commit: CommitDisplay;
  isLast?: boolean;
  isActive?: boolean;
  isCompareTarget?: boolean;
  onClick?: () => void;
  onCheckout?: () => void;
  onCompareWithCurrent?: () => void;
  onHardReset?: () => void;
}

const CommitItem: React.FC<CommitItemProps> = ({
  commit,
  isLast,
  isActive,
  isCompareTarget,
  onClick,
  onCheckout,
  onCompareWithCurrent,
  onHardReset,
}) => {
  const [datePart, ...timeParts] = commit.timestamp.split(" ");
  const timePart = timeParts.join(" ") || commit.timestamp;

  const containerClassName = `relative flex gap-2 pb-0 group cursor-pointer rounded-xl transition-all duration-200 p-3 mb-2 ${
    isActive
      ? "bg-blue-50/80 ring-1 ring-blue-200 shadow-sm"
      : isCompareTarget
        ? "bg-violet-50/90 ring-1 ring-violet-300 shadow-sm"
        : "hover:bg-slate-50/90"
  }`;

  const avatarClassName = `z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold transition-all duration-200 ${
    isActive
      ? "bg-blue-600 text-white shadow-sm"
      : isCompareTarget
        ? "bg-violet-600 text-white shadow-sm"
        : "bg-slate-100 text-slate-500 group-hover:bg-slate-200 group-hover:text-slate-700"
  }`;

  const authorClassName = `text-[13px] font-bold truncate transition-colors ${
    isActive ? "text-primary" : isCompareTarget ? "text-indigo-700" : "text-slate-900"
  }`;

  return (
    <ContextMenu>
      <ContextMenuTrigger>
        <div onClick={onClick} className={containerClassName}>
          {/* Connector Line */}
          {!isLast && (
            <div className="absolute left-[26px] top-[38px] bottom-[-8px] w-px bg-slate-200 transition-colors" />
          )}

          {/* Avatar / Icon */}
          <div className="flex flex-col items-center pt-0.5">
            <div className={avatarClassName}>{commit.initials}</div>
          </div>

          {/* Content */}
          <div className="flex min-w-0 flex-1 flex-col gap-0.5 py-0.5">
            <div className="flex items-center justify-between gap-2">
              <div className="flex min-w-0 items-center gap-1.5">
                <span className={authorClassName}>{commit.author}</span>
                {(isActive || isCompareTarget) && (
                  <span
                    className={`rounded-full px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide ${
                      isActive
                        ? "bg-blue-100 text-blue-700"
                        : "bg-indigo-100 text-indigo-700"
                    }`}
                  >
                    {isActive ? "Checked out" : "Compare"}
                  </span>
                )}
              </div>
              <span className="shrink-0 text-[10px] font-medium text-slate-400">
                {timePart}
              </span>
            </div>

            <span className="text-[10px] font-medium text-slate-400">
              {datePart || commit.timestamp}
            </span>

            <div
              className={`mt-0.5 min-w-0 truncate text-[12px] leading-4 transition-colors ${
                isActive
                  ? "text-slate-800"
                  : isCompareTarget
                    ? "text-violet-700"
                    : "text-slate-600"
              }`}
            >
              {commit.message}
            </div>
          </div>
        </div>
      </ContextMenuTrigger>
      <ContextMenuContent className="min-w-[220px]">
        <ContextMenuItem onSelect={onCheckout}>
          <GitCommit className="size-4 opacity-70" />
          Checkout
        </ContextMenuItem>
        <ContextMenuItem onSelect={onCompareWithCurrent}>
          <GitCompare className="size-4 opacity-70" />
          Compare with current
        </ContextMenuItem>
        <ContextMenuSeparator />
        <ContextMenuItem onSelect={onHardReset}>
          <History className="size-4 opacity-70" />
          Hard reset
        </ContextMenuItem>
      </ContextMenuContent>
    </ContextMenu>
  );
};

export default CommitItem;
