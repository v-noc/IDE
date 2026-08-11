import { memo } from "react";
import { format } from "date-fns";

interface NodeFooterProps {
  createdAt?: string;
  updatedAt?: string;
}

const formatStamp = (dateString?: string): string | null => {
  if (!dateString) return null;
  try {
    return format(new Date(dateString), "MMM d · h:mm a").toLowerCase();
  } catch {
    return null;
  }
};

export const NodeFooter = memo(function NodeFooter({
  createdAt,
  updatedAt,
}: NodeFooterProps) {
  const created = formatStamp(createdAt);
  const updated = formatStamp(updatedAt);
  if (!created && !updated) return null;

  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-border px-3 py-2 text-[11px] text-muted-foreground">
      {created && <span>created {created}</span>}
      {updated && <span>updated {updated}</span>}
    </div>
  );
});
