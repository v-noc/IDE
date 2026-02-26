import type { ReplayEvent } from "../../types/conversation";

const SPOTLIGHT_STYLE_ID = "agent-replay-focus-style";
const DIM_CLASS = "agent-replay-dimmed";
const HIGHLIGHT_CLASS = "agent-replay-highlighted";
const FOCUS_LAYER_CLASS = "agent-replay-focus-active";

let activeCleanup: (() => void) | null = null;

function ensureSpotlightStyle() {
  if (document.getElementById(SPOTLIGHT_STYLE_ID)) return;

  const style = document.createElement("style");
  style.id = SPOTLIGHT_STYLE_ID;
  style.textContent = `
    .${FOCUS_LAYER_CLASS} .react-flow__edges,
    .${FOCUS_LAYER_CLASS} .react-flow__background,
    .${FOCUS_LAYER_CLASS} .react-flow__controls {
      opacity: 0.18;
      transition: opacity 180ms ease;
    }

    .react-flow__node.${DIM_CLASS} {
      opacity: 0.16 !important;
      filter: blur(0.4px) saturate(0.7);
      transition: opacity 180ms ease, filter 180ms ease, transform 180ms ease;
    }

    .react-flow__node.${HIGHLIGHT_CLASS} {
      opacity: 1 !important;
      filter: none !important;
      z-index: 50 !important;
      transform: scale(1.03);
      box-shadow: 0 0 0 3px rgba(251, 191, 36, 0.95), 0 0 22px rgba(251, 191, 36, 0.45);
      transition: opacity 180ms ease, filter 180ms ease, transform 180ms ease, box-shadow 180ms ease;
    }
  `;

  document.head.appendChild(style);
}

function readNodeId(event: ReplayEvent): string | null {
  const payload = event.payload as { nodeId?: unknown; id?: unknown };
  if (typeof payload?.nodeId === "string" && payload.nodeId.length > 0) {
    return payload.nodeId;
  }
  if (typeof payload?.id === "string" && payload.id.length > 0) {
    return payload.id;
  }
  return null;
}

function cssEscape(value: string): string {
  if (typeof CSS !== "undefined" && typeof CSS.escape === "function") {
    return CSS.escape(value);
  }
  return value.replace(/["\\]/g, "\\$&");
}

export async function focusHandler(
  event: ReplayEvent,
  signal: AbortSignal,
): Promise<void> {
  if (signal.aborted) return;

  ensureSpotlightStyle();
  activeCleanup?.();

  const nodeId = readNodeId(event);

  if (!nodeId) return;

  // const escapedId = cssEscape(nodeId);
  const target = document.querySelector<HTMLElement>(
    `[data-id="${nodeId}"]`,
  );

  if (!target) return;

  const flowRoot =
    target.closest<HTMLElement>(".react-flow") ??
    document.querySelector<HTMLElement>(".react-flow");
  const allNodes = Array.from(
    document.querySelectorAll<HTMLElement>(".react-flow__node"),
  );

  for (const node of allNodes) {
    if (node === target) {
      node.classList.add(HIGHLIGHT_CLASS);
      node.classList.remove(DIM_CLASS);
      continue;
    }
    node.classList.add(DIM_CLASS);
    node.classList.remove(HIGHLIGHT_CLASS);
  }

  flowRoot?.classList.add(FOCUS_LAYER_CLASS);
  target.scrollIntoView({ behavior: "smooth", block: "center", inline: "center" });

  const cleanup = () => {
    for (const node of allNodes) {
      node.classList.remove(DIM_CLASS);
      node.classList.remove(HIGHLIGHT_CLASS);
    }
    flowRoot?.classList.remove(FOCUS_LAYER_CLASS);
    if (activeCleanup === cleanup) {
      activeCleanup = null;
    }
  };

  activeCleanup = cleanup;

  await new Promise<void>((resolve) => {
    const onAbort = () => {
      cleanup();
      resolve();
    };

    signal.addEventListener("abort", onAbort, { once: true });
    requestAnimationFrame(() => {
      signal.removeEventListener("abort", onAbort);
      resolve();
    });
  });
}
