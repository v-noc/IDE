import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import {
  highlightWalkthroughCode,
  isWalkthroughShikiLang,
} from "@/lib/walkthroughShiki";

export function useShikiHtml(
  code: string,
  language: string | undefined,
): string | null {
  const { resolvedTheme } = useTheme();
  const theme = resolvedTheme === "light" ? "github-light" : "github-dark";
  const lang = language?.toLowerCase();
  const [html, setHtml] = useState<string | null>(null);

  useEffect(() => {
    if (!lang || !isWalkthroughShikiLang(lang)) {
      setHtml(null);
      return;
    }

    let cancelled = false;
    void highlightWalkthroughCode(code, lang, theme).then((result) => {
      if (!cancelled) {
        setHtml(result);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [code, lang, theme]);

  return html;
}
