import { existsSync, readdirSync, statSync } from "node:fs";
import path from "node:path";
import { ModuleKind, Project, ScriptTarget } from "ts-morph";

function walkSourceFiles(dir: string, out: string[]): void {
  let names: string[];
  try {
    names = readdirSync(dir);
  } catch {
    return;
  }
  for (const name of names) {
    if (name === "node_modules" || name === ".git") continue;
    const p = path.join(dir, name);
    try {
      const st = statSync(p);
      if (st.isDirectory()) {
        walkSourceFiles(p, out);
      } else if (/\.(ts|tsx|js|jsx|mjs|cjs|mts|cts)$/.test(name)) {
        out.push(p);
      }
    } catch {
      continue;
    }
  }
}

/** Load a ts-morph `Project` for symbol resolution (tsconfig/jsconfig or recursive source scan). */
export function createMorphProject(projectRoot: string): Project {
  const root = path.normalize(projectRoot);
  const tsconfig = path.join(root, "tsconfig.json");
  const jsconfig = path.join(root, "jsconfig.json");

  if (existsSync(tsconfig)) {
    return new Project({ tsConfigFilePath: tsconfig });
  }
  if (existsSync(jsconfig)) {
    return new Project({ tsConfigFilePath: jsconfig });
  }

  const project = new Project({
    compilerOptions: {
      allowJs: true,
      target: ScriptTarget.Latest,
      module: ModuleKind.ESNext,
    },
    skipAddingFilesFromTsConfig: true,
  });
  const files: string[] = [];
  walkSourceFiles(root, files);
  for (const f of files) {
    try {
      project.addSourceFileAtPath(f);
    } catch {
      // unreadable or non-source
    }
  }
  return project;
}
