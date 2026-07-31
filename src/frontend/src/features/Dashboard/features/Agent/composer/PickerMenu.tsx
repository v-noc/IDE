import type { ReactNode } from "react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

interface PickerMenuProps {
  label: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  trigger: ReactNode;
  children: ReactNode;
  widthClassName?: string;
}

export function PickerMenu({
  label,
  open,
  onOpenChange,
  trigger,
  children,
  widthClassName = "w-[280px]",
}: PickerMenuProps) {
  return (
    <Popover open={open} onOpenChange={onOpenChange}>
      <PopoverTrigger asChild>{trigger}</PopoverTrigger>
      <PopoverContent
        side="top"
        align="start"
        className={cn(
          "agent-v2 border-agent-border-strong bg-agent-bg-card p-1.5 text-agent-text shadow-[0_16px_48px_rgba(0,0,0,0.55)]",
          widthClassName,
        )}
      >
        <p className="px-2.5 pt-2 pb-1.5 text-[10px] font-bold tracking-[0.08em] text-agent-text-label">
          {label}
        </p>
        <div className="space-y-0.5">{children}</div>
      </PopoverContent>
    </Popover>
  );
}
