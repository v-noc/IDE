import type { ComponentPropsWithoutRef } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import { useShikiHtml } from "./useShikiHighlighter";

const PLAIN_PRE_CLASS =
  "my-2 overflow-x-auto rounded-md bg-muted p-3 font-mono text-xs leading-relaxed";

function HighlightedPre({
  code,
  language,
}: {
  code: string;
  language: string;
}) {
  const html = useShikiHtml(code, language);

  if (html) {
    return (
      <div
        className="my-2 overflow-x-auto rounded-md text-xs leading-relaxed [&_pre]:!m-0 [&_pre]:!bg-transparent"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    );
  }

  return (
    <pre className={PLAIN_PRE_CLASS}>
      <code>{code}</code>
    </pre>
  );
}

function CodeRenderer({
  className,
  children,
  ...props
}: ComponentPropsWithoutRef<"code">) {
  const match = /language-(\w+)/.exec(className ?? "");
  const code = String(children).replace(/\n$/, "");

  if (!match) {
    return (
      <code
        className="rounded bg-muted px-1 py-0.5 font-mono text-[0.85em]"
        {...props}
      >
        {children}
      </code>
    );
  }

  return <HighlightedPre code={code} language={match[1]} />;
}

const markdownComponents: Components = {
  a: (props) => (
    <a
      {...props}
      target="_blank"
      rel="noreferrer"
      className="underline underline-offset-2"
    />
  ),
  p: (props) => <p className="mb-2 last:mb-0" {...props} />,
  ul: (props) => <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0" {...props} />,
  ol: (props) => (
    <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0" {...props} />
  ),
  li: (props) => <li className="leading-relaxed" {...props} />,
  strong: (props) => <strong className="font-semibold" {...props} />,
  code: CodeRenderer,
  pre: ({ children }) => <>{children}</>,
};

export function StepMarkdown({ text }: { text: string }) {
  return (
    <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
      {text}
    </ReactMarkdown>
  );
}
