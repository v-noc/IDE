import { writeFileSync } from "node:fs";
import path from "node:path";
import { ModuleKind, Project, ScriptTarget, type SourceFile } from "ts-morph";
import { buildNodesFromSourceFile } from "./ast/buildScope";
import {
  createMorphProject,
  createRootFrame,
  findCallExpressionAt,
  mergeFrameStack,
  resolveCallHierarchyForNode,
  toCallFrameStackWire,
} from "./call_resolver";
import { injectIdsIntoSource } from "./idInjector";
import type { InitializeResult, ParseFileResult, ResolveCallsResult } from "./models";
import type { InitializeParams, ParseFileParams, ResolveCallsParams } from "../types";

function writeIfModified(filePath: string, content: string): void {
  try {
    writeFileSync(filePath, content, "utf8");
  } catch {
    // Mirror Python: swallow; content is still returned to the client.
  }
}

function createProject(): Project {
  return new Project({
    useInMemoryFileSystem: true,
    compilerOptions: {
      allowJs: true,
      target: ScriptTarget.Latest,
      module: ModuleKind.ESNext,
    },
  });
}

function parseSourceToNodes(
  filePath: string,
  content: string,
  resolveMro: boolean,
): SourceFile {
  const project = createProject();
  return project.createSourceFile(filePath, content, { overwrite: true });
}

export class TsJsDriver {
  private projectPath: string | null = null;
  /** Lazily built for `resolve_calls` symbol resolution. */
  private morphProject: Project | null = null;

  initialize(params: InitializeParams): InitializeResult {
    this.projectPath = params.project_path;
    this.morphProject = null;
    return {
      status: "ok",
      extensions: [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"],
    };
  }

  private ensureProjectRoot(): string {
    if (!this.projectPath) {
      throw new Error("Driver not initialized");
    }
    return this.projectPath;
  }

  private ensureMorphProject(): Project {
    const root = this.ensureProjectRoot();
    if (!this.morphProject) {
      this.morphProject = createMorphProject(root);
    }
    return this.morphProject;
  }

  resolveCalls(params: ResolveCallsParams): ResolveCallsResult {
    const projectRoot = this.ensureProjectRoot();
    const project = this.ensureMorphProject();
    const absFile = path.resolve(params.file_path);

    const normalized = path.normalize(absFile);
    let sf =
      project.getSourceFile(normalized) ??
      project
        .getSourceFiles()
        .find((f) => path.normalize(f.getFilePath()) === normalized);
    if (!sf) {
      try {
        sf = project.addSourceFileAtPath(normalized);
      } catch {
        return { call_frame_stack: toCallFrameStackWire(createRootFrame()) };
      }
    }
    if (!sf) {
      return { call_frame_stack: toCallFrameStackWire(createRootFrame()) };
    }

    const merged = createRootFrame();

    for (const raw of params.calls) {
      if (!raw || typeof raw !== "object") continue;
      const d = raw as Record<string, unknown>;
      if (d.type !== "call") continue;
      const pos = d.position as Record<string, unknown> | undefined;
      const line =
        pos && typeof pos.line === "number" ? pos.line : undefined;
      const callColPos =
        typeof d.call_col_pos === "number" ? d.call_col_pos : undefined;
      if (line === undefined || callColPos === undefined) continue;

      const sub = createRootFrame();
      const expr = findCallExpressionAt(sf, line, callColPos);
      if (expr) {
        try {
          resolveCallHierarchyForNode(expr, sub, projectRoot);
        } catch {
          // one site failed; continue with others (Python logs and continues)
        }
      }
      mergeFrameStack(merged, sub);
    }

    return { call_frame_stack: toCallFrameStackWire(merged) };
  }

  parseFile(params: ParseFileParams): ParseFileResult {
    const resolveMro = params.resolve_mro === true;
    const { source: processed, modified } = injectIdsIntoSource(
      params.content,
      params.file_path,
    );
    if (modified && params.file_path) {
      writeIfModified(params.file_path, processed);
    }
    const sf = parseSourceToNodes(params.file_path, processed, resolveMro);
    const nodes = buildNodesFromSourceFile(sf, resolveMro);
    return {
      nodes,
      content: processed,
      modified,
    };
  }
}
