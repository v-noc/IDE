import { cn } from "@/lib/utils";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { Components } from "react-markdown";

const markdownComponents: Components = {
  p: ({ children, className, ...props }) => (
    <p className={cn("mb-2 text-xs leading-relaxed last:mb-0", className)} {...props}>
      {children}
    </p>
  ),
  ul: ({ children, className, ...props }) => (
    <ul className={cn("mb-2 list-disc pl-4 text-xs leading-relaxed last:mb-0", className)} {...props}>
      {children}
    </ul>
  ),
  ol: ({ children, className, ...props }) => (
    <ol className={cn("mb-2 list-decimal pl-4 text-xs leading-relaxed last:mb-0", className)} {...props}>
      {children}
    </ol>
  ),
  li: ({ children, className, ...props }) => (
    <li className={cn("mt-0.5", className)} {...props}>
      {children}
    </li>
  ),
  a: ({ href, children, className, ...props }) => {
    const external = href?.startsWith("http://") || href?.startsWith("https://");
    return (
      <a
        href={href}
        className={cn("text-primary underline underline-offset-2 hover:opacity-90", className)}
        target={external ? "_blank" : undefined}
        rel={external ? "noopener noreferrer" : undefined}
        {...props}
      >
        {children}
      </a>
    );
  },
  code: ({ className, children, ...props }) => {
    const inline = !className;
    if (inline) {
      return (
        <code
          className={cn(
            "rounded bg-muted px-1 py-0.5 font-mono text-[11px] text-foreground",
            className,
          )}
          {...props}
        >
          {children}
        </code>
      );
    }
    return (
      <code className={cn("font-mono text-[11px]", className)} {...props}>
        {children}
      </code>
    );
  },
  pre: ({ children, className, ...props }) => (
    <pre
      className={cn(
        "mb-2 max-w-full overflow-x-auto rounded-md border border-border bg-muted/80 p-2 text-[11px] last:mb-0",
        className,
      )}
      {...props}
    >
      {children}
    </pre>
  ),
  blockquote: ({ children, className, ...props }) => (
    <blockquote
      className={cn("mb-2 border-l-2 border-border pl-3 text-muted-foreground last:mb-0", className)}
      {...props}
    >
      {children}
    </blockquote>
  ),
  h1: ({ children, className, ...props }) => (
    <h1 className={cn("mb-2 text-sm font-semibold last:mb-0", className)} {...props}>
      {children}
    </h1>
  ),
  h2: ({ children, className, ...props }) => (
    <h2 className={cn("mb-2 text-xs font-semibold last:mb-0", className)} {...props}>
      {children}
    </h2>
  ),
  h3: ({ children, className, ...props }) => (
    <h3 className={cn("mb-1.5 text-xs font-semibold last:mb-0", className)} {...props}>
      {children}
    </h3>
  ),
  table: ({ children, className, ...props }) => (
    <div className="mb-2 max-w-full overflow-x-auto last:mb-0">
      <table className={cn("w-full border-collapse border border-border text-xs", className)} {...props}>
        {children}
      </table>
    </div>
  ),
  th: ({ children, className, ...props }) => (
    <th className={cn("border border-border bg-muted/60 px-2 py-1 text-left font-semibold", className)} {...props}>
      {children}
    </th>
  ),
  td: ({ children, className, ...props }) => (
    <td className={cn("border border-border px-2 py-1 align-top", className)} {...props}>
      {children}
    </td>
  ),
  hr: ({ className, ...props }) => (
    <hr className={cn("my-3 border-border", className)} {...props} />
  ),
};

export interface AssistantMarkdownProps {
  text: string;
  className?: string;
}

/** Renders assistant message body as GitHub-flavored Markdown. */
export function AssistantMarkdown({ text, className }: AssistantMarkdownProps) {
  return (
    <div
      className={cn(
        "agent-markdown text-foreground [&>*:first-child]:mt-0",
        className,
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {text}
      </ReactMarkdown>
    </div>
  );
}
