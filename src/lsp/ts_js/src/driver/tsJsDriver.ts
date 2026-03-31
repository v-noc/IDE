import { writeFileSync } from "node:fs";
import { ModuleKind, Project, ScriptTarget, type SourceFile } from "ts-morph";
import { buildNodesFromSourceFile } from "./ast/buildScope";
import { injectIdsIntoSource } from "./idInjector";
import type { InitializeResult, ParseFileResult } from "./models";
import type { InitializeParams, ParseFileParams } from "../types";

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

  initialize(params: InitializeParams): InitializeResult {
    this.projectPath = params.project_path;
    void this.projectPath;
    return {
      status: "ok",
      extensions: [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"],
    };
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
