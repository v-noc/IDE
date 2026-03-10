import React from "react";
import type { CommitDisplay } from "../store/useVersioningStore";

interface CommitItemProps {
  commit: CommitDisplay;
  isLast?: boolean;
  isActive?: boolean;
  onClick?: () => void;
}

const CommitItem: React.FC<CommitItemProps> = ({
  commit,
  isLast,
  isActive,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={`relative flex gap-2 pb-0 group cursor-pointer rounded-xl transition-all duration-200 p-3 mb-2 ${
        isActive
          ? "bg-primary/5 ring-1 ring-primary/20 shadow-sm"
          : "hover:bg-slate-50"
      }`}
    >
      {/* Connector Line */}
      {!isLast && (
        <div className="absolute left-[31px] top-[48px] bottom-[-8px] w-px bg-slate-100 group-hover:bg-slate-200 transition-colors" />
      )}

      {/* Avatar / Icon */}
      <div className="flex flex-col items-center">
        <div
          className={`z-10 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold transition-all duration-200 ${
            isActive
              ? "bg-primary text-white shadow-md"
              : "bg-slate-100 text-slate-500 group-hover:bg-slate-200 group-hover:text-slate-700"
          }`}
        >
          {commit.initials}
        </div>
      </div>

      {/* Content */}
      <div className="flex flex-1 flex-col gap-0.5 min-w-0">
        <div className="flex items-center justify-between gap-2">
          <span
            className={`text-[13px] font-bold truncate transition-colors ${
              isActive ? "text-primary" : "text-slate-900"
            }`}
          >
            {commit.author}
          </span>
          <span className="shrink-0 text-[10px] font-medium text-slate-400 uppercase tracking-tight">
            {commit.timestamp.split(" ").slice(1).join(" ") || commit.timestamp}
          </span>
        </div>

        <span className="text-[11px] font-medium text-slate-400">
          {commit.timestamp.split(" ")[0] || commit.timestamp}
        </span>

        <div
          className={`mt-1 rounded-lg py-1 text-[13px] leading-snug transition-colors ${
            isActive ? "text-slate-800" : "text-slate-600"
          }`}
        >
          {commit.message}
        </div>
      </div>
    </div>
  );
};

export default CommitItem;
