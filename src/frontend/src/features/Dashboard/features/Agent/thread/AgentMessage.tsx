import type { ReactNode } from "react";

interface AgentMessageProps {
  children: ReactNode;
}

export function AgentMessage({ children }: AgentMessageProps) {
  return (
    <article className="shrink-0 px-1 py-0.5">
      <div className="mb-1.5 text-[10.5px] font-bold tracking-[0.08em] text-agent-text-agent-label">
        AGENT
      </div>
      {children}
    </article>
  );
}
