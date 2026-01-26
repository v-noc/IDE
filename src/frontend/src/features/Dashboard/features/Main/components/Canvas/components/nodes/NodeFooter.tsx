import { memo } from "react";
import { Calendar, Clock } from "lucide-react";
import { format } from "date-fns";

interface NodeFooterProps {
  createdAt?: string;
  updatedAt?: string;
  borderColor: string;
  iconColor: string;
  textColor: string;
}

const formatDateTime = (dateString?: string): string => {
  if (!dateString) return "N/A";
  try {
    const date = new Date(dateString);
    return format(date, "MMM d, yyyy 'at' h:mm a");
  } catch {
    return "N/A";
  }
};

export const NodeFooter = memo(function NodeFooter({
  createdAt,
  updatedAt,
  borderColor,
  textColor,
  iconColor,
}: NodeFooterProps) {
  if (!createdAt && !updatedAt) return null;

  return (
    <div
      className="flex items-center justify-between gap-4 border-t px-4 py-2.5 text-[10px] bg-slate-50/30"
      style={{ borderColor }}
    >
      {createdAt && (
        <div className="flex items-center gap-1.5 text-slate-500" >
          <Calendar size={11} style={{ color: iconColor }} />
          <span className="font-medium" style={{ color: textColor }}>
            Created {formatDateTime(createdAt)}
          </span>
        </div>
      )}
      {updatedAt && (
        <div className="flex items-center gap-1.5 text-slate-500" >
          <Clock size={11} style={{ color: iconColor }} />
          <span className="font-medium" style={{ color: textColor }}>
            Updated {formatDateTime(updatedAt)}
          </span>
        </div>
      )}
    </div>
  );
});
