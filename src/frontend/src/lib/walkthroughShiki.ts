import {
  createSingletonShorthands,
  createdBundledHighlighter,
} from "@shikijs/core";
import { createJavaScriptRegexEngine } from "@shikijs/engine-javascript";

type BundledLanguage =
  | "python"
  | "py"
  | "javascript"
  | "js"
  | "typescript"
  | "ts"
  | "json"
  | "bash"
  | "sh";
type BundledTheme = "github-light" | "github-dark";

const bundledLanguages = {
  python: () => import("@shikijs/langs/python"),
  py: () => import("@shikijs/langs/python"),
  javascript: () => import("@shikijs/langs/javascript"),
  js: () => import("@shikijs/langs/javascript"),
  typescript: () => import("@shikijs/langs/typescript"),
  ts: () => import("@shikijs/langs/typescript"),
  json: () => import("@shikijs/langs/json"),
  bash: () => import("@shikijs/langs/bash"),
  sh: () => import("@shikijs/langs/bash"),
};

const bundledThemes = {
  "github-light": () => import("@shikijs/themes/github-light"),
  "github-dark": () => import("@shikijs/themes/github-dark"),
};

const createHighlighter = createdBundledHighlighter<
  BundledLanguage,
  BundledTheme
>({
  langs: bundledLanguages,
  themes: bundledThemes,
  engine: () => createJavaScriptRegexEngine(),
});

const { codeToHtml } = createSingletonShorthands<BundledLanguage, BundledTheme>(
  createHighlighter,
);

const SUPPORTED_LANGS = new Set<string>(Object.keys(bundledLanguages));

export function isWalkthroughShikiLang(lang: string): boolean {
  return SUPPORTED_LANGS.has(lang.toLowerCase());
}

export async function highlightWalkthroughCode(
  code: string,
  lang: string,
  theme: BundledTheme,
): Promise<string | null> {
  const normalized = lang.toLowerCase();
  if (!SUPPORTED_LANGS.has(normalized)) {
    return null;
  }
  return codeToHtml(code, {
    lang: normalized as BundledLanguage,
    theme,
  });
}
