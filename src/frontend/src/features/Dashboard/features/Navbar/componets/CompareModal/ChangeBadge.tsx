type ChangeBadgeProps = {
  type: "added" | "removed" | "modified";
};

const CLASSES: Record<ChangeBadgeProps["type"], string> = {
  added: "bg-green-100 text-green-700 border-green-200",
  removed: "bg-red-100 text-red-700 border-red-200",
  modified: "bg-amber-100 text-amber-700 border-amber-200",
};

const SYMBOL: Record<ChangeBadgeProps["type"], string> = {
  added: "+",
  removed: "-",
  modified: "~",
};

const ChangeBadge = ({ type }: ChangeBadgeProps) => (
  <span
    className={`text-[10px] px-1.5 py-0.5 rounded border inline-flex items-center gap-1 ${CLASSES[type]}`}
  >
    <span>{SYMBOL[type]}</span>
    <span className="capitalize">{type}</span>
  </span>
);

export default ChangeBadge;
