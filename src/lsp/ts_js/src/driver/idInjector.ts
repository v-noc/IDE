import {
  Node,
  Project,
  ScriptTarget,
  ModuleKind,
  type JSDocableNode,
  type SourceFile,
} from "ts-morph";

const ID_RE = /ID:\s*\S+/;

function hasJsDocId(node: JSDocableNode): boolean {
  return node.getJsDocs().some((d) => ID_RE.test(d.getInnerText()));
}

/** Append `ID: <uuid>` to existing JSDoc or add a new block (Python `libcst` parity). */
function ensureJsDocId(node: JSDocableNode): boolean {
  if (hasJsDocId(node)) return false;
  const id = crypto.randomUUID();
  const docs = node.getJsDocs();
  if (docs.length === 0) {
    node.addJsDoc({ description: `ID: ${id}` });
    return true;
  }
  const first = docs[0];
  const prev = first.getInnerText().trimEnd();
  const merged = prev ? `${prev}\n\nID: ${id}` : `ID: ${id}`;
  first.remove();
  node.insertJsDoc(0, { description: merged });
  return true;
}

function collectJsDocTargets(sf: SourceFile): JSDocableNode[] {
  const out: JSDocableNode[] = [];
  sf.forEachDescendant((node) => {
    if (Node.isClassDeclaration(node)) {
      out.push(node);
      return;
    }
    if (Node.isFunctionDeclaration(node)) {
      if (node.getBody()) out.push(node);
      return;
    }
    if (Node.isMethodDeclaration(node)) {
      out.push(node);
      return;
    }
    if (Node.isConstructorDeclaration(node)) {
      out.push(node);
    }
  });
  return out;
}

export function injectIdsIntoSource(source: string, filePath: string): {
  source: string;
  modified: boolean;
} {
  const project = new Project({
    useInMemoryFileSystem: true,
    compilerOptions: {
      allowJs: true,
      target: ScriptTarget.Latest,
      module: ModuleKind.ESNext,
    },
  });

  let sf: SourceFile;
  try {
    sf = project.createSourceFile(filePath, source, { overwrite: true });
  } catch {
    return { source, modified: false };
  }

  let modified = false;
  for (const node of collectJsDocTargets(sf)) {
    if (ensureJsDocId(node)) modified = true;
  }

  return { source: sf.getFullText(), modified };
}
