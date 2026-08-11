interface InlineAddRowProps {
  label: string;
  onClick: () => void;
}

export function InlineAddRow({ label, onClick }: InlineAddRowProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full px-3 py-2 text-left text-xs text-muted-foreground hover:text-foreground hover:bg-muted/20"
    >
      + {label}
    </button>
  );
}
