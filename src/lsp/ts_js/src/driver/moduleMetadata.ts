/**
 * Module-level metadata in a leading JSDoc block (`FileID:` / `FolderID:`), mirroring
 * Python `inject_module_metadata` + `IDInjector._extract_metadata` on module docstrings.
 */

function escapeRegex(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function dedent(s: string): string {
  const lines = s.split("\n");
  const nonEmpty = lines.filter((l) => l.trim().length > 0);
  if (nonEmpty.length === 0) return s.trim();
  const min = Math.min(
    ...nonEmpty.map((l) => {
      const m = l.match(/^\s*/);
      return m ? m[0].length : 0;
    }),
  );
  return lines.map((l) => (l.length >= min ? l.slice(min) : l)).join("\n").trim();
}

export function extractMetadata(doc: string): Record<string, string> {
  if (!doc.trim()) return {};
  const pairs = [...doc.matchAll(/(\S+)\s*:\s*(\S+)/g)];
  return Object.fromEntries(pairs.map((m) => [m[1], m[2]]));
}

function buildDocstring(
  originalDoc: string | null | undefined,
  newMetadata: Record<string, string>,
): string {
  let content = (originalDoc ?? "").replace(/\s+$/u, "");
  for (const key of Object.keys(newMetadata)) {
    const pattern = new RegExp(
      `(^|(?<=\\s))${escapeRegex(key)}\\s*:\\s*\\S+(?=\\s|$)`,
      "gm",
    );
    content = content.replace(pattern, "");
  }
  const kvText = Object.entries(newMetadata)
    .map(([k, v]) => `${k}: ${v}`)
    .join("\n");
  if (content.trim()) {
    return `${dedent(content)}\n\n${kvText}`;
  }
  return kvText;
}

function normalizeJsDocInner(raw: string): string {
  return raw
    .split("\n")
    .map((line) => line.replace(/^\s*\* ?/, "").trimEnd())
    .join("\n")
    .trim();
}

function formatJsDocBlock(inner: string): string {
  const trimmed = inner.trim();
  if (!trimmed) return "/**\n */\n";
  const lines = trimmed.split("\n");
  return `/**\n${lines.map((l) => ` * ${l}`).join("\n")}\n */`;
}

export function splitShebangAndBom(content: string): {
  prefix: string;
  rest: string;
} {
  let s = content;
  let prefix = "";
  if (s.charCodeAt(0) === 0xfeff) {
    prefix = "\uFEFF";
    s = s.slice(1);
  }
  const sh = s.match(/^#![^\n]*\n/);
  if (sh) {
    prefix += sh[0];
    s = s.slice(sh[0].length);
  }
  return { prefix, rest: s };
}

/** Strip the first leading JSDoc from the file body (after shebang/BOM). */
export function peelLeadingJsDoc(rest: string): {
  block: string | null;
  inner: string;
  after: string;
} {
  const m = rest.match(/^(\s*\/\*\*[\s\S]*?\*\/\s*\n?)/);
  if (!m) return { block: null, inner: "", after: rest };
  const block = m[1];
  const innerMatch = block.match(/\/\*\*([\s\S]*?)\*\//);
  const inner = innerMatch ? normalizeJsDocInner(innerMatch[1]) : "";
  return { block, inner, after: rest.slice(block.length) };
}

export function injectModuleMetadata(
  content: string,
  metadata: Record<string, string>,
): { content: string; modified: boolean } {
  try {
    const { prefix, rest } = splitShebangAndBom(content);
    const { block, inner, after } = peelLeadingJsDoc(rest);
    const currentMeta = extractMetadata(inner);
    let needsUpdate = false;
    for (const [k, v] of Object.entries(metadata)) {
      if (currentMeta[k] !== v) {
        needsUpdate = true;
        break;
      }
    }
    if (!needsUpdate) return { content, modified: false };

    const newInner = buildDocstring(inner || null, metadata);
    const newBlock = formatJsDocBlock(newInner);
    const newRest = block !== null ? `${newBlock}\n${after}` : `${newBlock}\n${rest}`;
    return { content: prefix + newRest, modified: true };
  } catch {
    return { content, modified: false };
  }
}
