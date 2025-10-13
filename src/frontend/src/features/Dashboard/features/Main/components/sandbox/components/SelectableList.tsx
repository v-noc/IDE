import { useMemo } from "react";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

export interface SelectableItem {
  id: string;
  label: string;
}

interface SelectableListProps {
  items: SelectableItem[];
  selectedId?: string;
  onSelect: (id: string) => void;
  onRemove?: (id: string) => void;
  className?: string;
  emptyText?: string;
  removable?: boolean;
  isItemRemovable?: (item: SelectableItem) => boolean;
}

export default function SelectableList({
  items,
  selectedId,
  onSelect,
  onRemove,
  className,
  emptyText = "No items",
  removable = true,
  isItemRemovable,
}: SelectableListProps) {
  const hasItems = useMemo(() => items.length > 0, [items.length]);

  if (!hasItems) {
    return (
      <div className={cn("text-sm text-muted-foreground p-2", className)}>
        {emptyText}
      </div>
    );
  }

  return (
    <ul className={cn("space-y-1", className)}>
      {items.map((item) => {
        const isActive = item.id === selectedId;
        const canRemove =
          Boolean(onRemove) &&
          removable &&
          (isItemRemovable ? isItemRemovable(item) : true);
        return (
          <li key={item.id}>
            <button
              type="button"
              onClick={() => onSelect(item.id)}
              className={cn(
                "w-full flex items-center justify-between rounded border px-2 py-1 text-left text-sm",
                isActive ? "bg-accent/60 border-primary" : "hover:bg-accent/40"
              )}
            >
              <span className="truncate pr-2">{item.label}</span>
              {canRemove ? (
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="h-6 w-6"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (onRemove) onRemove(item.id);
                  }}
                >
                  <X className="h-3.5 w-3.5" />
                </Button>
              ) : null}
            </button>
          </li>
        );
      })}
    </ul>
  );
}
