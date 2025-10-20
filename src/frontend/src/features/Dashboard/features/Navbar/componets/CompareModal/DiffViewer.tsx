type DiffViewerProps = {
  diff?: string;
};

const parseUnified = (diff?: string) => {
  if (!diff)
    return { left: [], right: [] } as { left: string[]; right: string[] };
  const lines = diff.split("\n");
  const left: string[] = [];
  const right: string[] = [];
  for (const line of lines) {
    if (
      line.startsWith("+++ ") ||
      line.startsWith("--- ") ||
      line.startsWith("diff ") ||
      line.startsWith("index ") ||
      line.startsWith("@@")
    ) {
      continue;
    }
    if (line.startsWith("+")) {
      left.push("");
      right.push(line);
    } else if (line.startsWith("-")) {
      left.push(line);
      right.push("");
    } else {
      left.push(line);
      right.push(line);
    }
  }
  return { left, right };
};

const lineClass = (s: string) =>
  s.startsWith("+")
    ? "bg-green-50 text-green-700"
    : s.startsWith("-")
    ? "bg-red-50 text-red-700"
    : "";

const DiffViewer = ({ diff }: DiffViewerProps) => {
  const { left, right } = parseUnified(diff);
  return (
    <div className="grid grid-cols-2 gap-2 text-xs h-full">
      <div className="border rounded overflow-auto">
        <table className="w-full text-left">
          <tbody>
            {left.map((l, i) => (
              <tr key={`l-${i}`} className={lineClass(l)}>
                <td className="px-2 py-0.5 whitespace-pre">{l || "\u00A0"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="border rounded overflow-auto">
        <table className="w-full text-left">
          <tbody>
            {right.map((r, i) => (
              <tr key={`r-${i}`} className={lineClass(r)}>
                <td className="px-2 py-0.5 whitespace-pre">{r || "\u00A0"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default DiffViewer;
