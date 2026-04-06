import { SyntaxKind, type CallExpression, type SourceFile } from "ts-morph";
import { createRootFrame, type CallFrameNode } from "./frame";
import { resolveCallHierarchyForNode, resolveNewHierarchyForNode } from "./resolveHierarchy";

export interface BuildCallTreeOptions {
  /** If set, only expand these call sites; otherwise every `CallExpression` in the file. */
  seedCalls?: CallExpression[];
  /** Include `new Foo()` sites. Default true. */
  includeNewExpressions?: boolean;
}

/**
 * Build a call tree from a source file: root → seed sites → recursive local callees.
 * Local = declaration under `projectRoot` and not under `node_modules`.
 */
export function buildFullCallTreeFromSourceFile(
  projectRoot: string,
  sourceFile: SourceFile,
  options: BuildCallTreeOptions = {},
): CallFrameNode {
  const root = createRootFrame();
  const seeds =
    options.seedCalls ?? sourceFile.getDescendantsOfKind(SyntaxKind.CallExpression);
  const visitedPair = new Set<string>();

  for (const call of seeds) {
    const key = `${call.getStart()}:${call.getEnd()}`;
    if (visitedPair.has(key)) continue;
    visitedPair.add(key);
    resolveCallHierarchyForNode(call, root, projectRoot);
  }

  if (options.includeNewExpressions !== false) {
    const news = sourceFile.getDescendantsOfKind(SyntaxKind.NewExpression);
    for (const ne of news) {
      const key = `new:${ne.getStart()}:${ne.getEnd()}`;
      if (visitedPair.has(key)) continue;
      visitedPair.add(key);
      resolveNewHierarchyForNode(ne, root, projectRoot);
    }
  }

  return root;
}
