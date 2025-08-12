/* eslint-disable react-refresh/only-export-components */
import { useCallback, useEffect, useRef, useState } from "react";
import mermaid from "mermaid";
import {
  createReactBlockSpec,
  type ReactCustomBlockRenderProps,
} from "@blocknote/react";
import { Eye, Pencil } from "lucide-react";
import type { InlineContentSchema, StyleSchema } from "@blocknote/core";
// Using a styled native code block for editing instead of a 3rd-party editor

type TextAlignment = "left" | "center" | "right" | "justify";

// Define the Mermaid block configuration
export const mermaidBlockConfig = {
  type: "mermaid" as const,
  content: "none" as const,
  propSchema: {
    // Alignment similar to image/file blocks
    textAlignment: {
      default: "left" as TextAlignment,
      values: ["left", "center", "right", "justify"] as const,
    },
    // Mermaid code content
    code: {
      default: "flowchart TD\nA[Start] --> B[Do something] --> C[End]" as const,
    },
    // Preview toggle
    showPreview: {
      default: true as const,
    },
    // Resizable preview width in px
    previewWidth: {
      default: undefined as unknown as number | undefined,
      type: "number" as const,
    },
  },
};

function useMermaid(
  code: string,
  colorScheme: "light" | "dark",
  renderKey: string | number
) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: colorScheme === "dark" ? "dark" : "default",
    });
  }, [colorScheme]);

  useEffect(() => {
    let cancelled = false;
    const render = async () => {
      if (!containerRef.current) return;
      try {
        const id = `mermaid-${Math.random().toString(36).slice(2)}`;
        const { svg } = await mermaid.render(id, code);
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = svg;
        }
      } catch {
        if (!cancelled && containerRef.current) {
          containerRef.current.innerHTML = `<div style="color: #b91c1c">Mermaid render error</div>`;
        }
      }
    };
    render();
    return () => {
      cancelled = true;
    };
  }, [code, renderKey]);

  return containerRef;
}

const ResizableHandles = ({
  onResizeStart,
}: {
  onResizeStart: (
    handle: "left" | "right",
    clientX: number,
    initialWidth: number
  ) => void;
}) => {
  const ref = useRef<HTMLDivElement | null>(null);
  const getWidth = () => ref.current?.parentElement?.clientWidth || 0;
  return (
    <div ref={ref} className="relative">
      <div
        className="bn-resize-handle"
        style={{ left: 0 }}
        onMouseDown={(e) => onResizeStart("left", e.clientX, getWidth())}
      />
      <div
        className="bn-resize-handle"
        style={{ right: 0 }}
        onMouseDown={(e) => onResizeStart("right", e.clientX, getWidth())}
      />
    </div>
  );
};

export const MermaidBlockComponent = (
  props: ReactCustomBlockRenderProps<
    typeof mermaidBlockConfig,
    InlineContentSchema,
    StyleSchema
  >
) => {
  const [mode, setMode] = useState<"edit" | "preview">(
    props.block.props.showPreview ? "preview" : "edit"
  );
  const [localCode, setLocalCode] = useState<string>(props.block.props.code);
  // hovered retained for potential future UX, but not used
  const [resize, setResize] = useState<
    | { initialWidth: number; initialClientX: number; handle: "left" | "right" }
    | undefined
  >(undefined);
  const [width, setWidth] = useState<number | undefined>(
    props.block.props.previewWidth
  );
  const previewRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  // Detect theme from container attribute set by BlockNoteView
  const colorScheme: "light" | "dark" =
    (props.editor.domElement?.closest(".bn-container") as HTMLElement | null)
      ?.dataset?.colorScheme === "dark"
      ? "dark"
      : "light";

  // Keep local code in sync if external updates occur
  useEffect(() => {
    if (props.block.props.code !== localCode) {
      setLocalCode(props.block.props.code);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.block.props.code]);

  const mermaidRef = useMermaid(localCode, colorScheme, mode);

  useEffect(() => {
    if (resize) {
      const onMove = (e: MouseEvent) => {
        e.preventDefault();
        let newWidth = resize.initialWidth;
        const dx = e.clientX - resize.initialClientX;

        if (props.block.props.textAlignment === "center") {
          newWidth += resize.handle === "left" ? -2 * dx : 2 * dx;
        } else if (
          (props.block.props.textAlignment === "left" &&
            resize.handle === "right") ||
          (props.block.props.textAlignment === "right" &&
            resize.handle === "left")
        ) {
          newWidth += resize.handle === "left" ? -dx : dx;
        }

        const editorWidth =
          props.editor.domElement?.firstElementChild?.clientWidth;
        if (editorWidth) {
          setWidth(Math.max(64, Math.min(newWidth, editorWidth)));
        }
      };

      const onUp = () => {
        setResize(undefined);
        if (width) {
          props.editor.updateBlock(props.block, {
            props: { previewWidth: width },
          });
        }
      };

      window.addEventListener("mousemove", onMove);
      window.addEventListener("mouseup", onUp, { once: true });

      return () => {
        window.removeEventListener("mousemove", onMove);
        window.removeEventListener("mouseup", onUp);
      };
    }
  }, [resize, width, props.editor, props.block]);

  const startResize = useCallback(
    (handle: "left" | "right", clientX: number, initialWidth: number) => {
      setResize({ handle, initialClientX: clientX, initialWidth });
    },
    []
  );

  const setCode = (code: string) => {
    setLocalCode(code);
    props.editor.updateBlock(props.block, { props: { code } });
  };

  const autoResizeTextarea = useCallback(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    const minHeight = 260;
    el.style.height = Math.max(el.scrollHeight, minHeight) + "px";
  }, []);

  useEffect(() => {
    autoResizeTextarea();
  }, [localCode, autoResizeTextarea]);

  const toggleMode = (m: "edit" | "preview") => {
    setMode(m);
    props.editor.updateBlock(props.block, {
      props: { showPreview: m === "preview" },
    });
  };

  return (
    <div className="bn-file-block-content-wrapper">
      <div className="flex items-center gap-2 mb-2">
        <div className="inline-flex rounded-md border bg-background overflow-hidden shadow-sm">
          <button
            className={`px-2 py-1 text-sm flex items-center gap-1 ${
              mode === "edit" ? "bg-accent" : ""
            }`}
            title="Edit"
            onClick={() => toggleMode("edit")}
          >
            <Pencil className="h-4 w-4" />
          </button>
          <button
            className={`px-2 py-1 text-sm flex items-center gap-1 ${
              mode === "preview" ? "bg-accent" : ""
            }`}
            title="Preview"
            onClick={() => toggleMode("preview")}
          >
            <Eye className="h-4 w-4" />
          </button>
        </div>
        {/* Alignment controls are intentionally not rendered here.
            Use the editor's formatting toolbar above for alignment. */}
      </div>

      {mode === "edit" ? (
        <div className="rounded-md border bg-card p-2">
          <textarea
            ref={textareaRef}
            value={localCode}
            onChange={(e) => setCode(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Tab") {
                e.preventDefault();
                const target = e.target as HTMLTextAreaElement;
                const start = target.selectionStart ?? 0;
                const end = target.selectionEnd ?? 0;
                const indent = "  ";
                const newValue =
                  target.value.substring(0, start) +
                  indent +
                  target.value.substring(end);
                setCode(newValue);
                // restore caret position after React update
                requestAnimationFrame(() => {
                  target.selectionStart = target.selectionEnd =
                    start + indent.length;
                });
              }
            }}
            className="w-full rounded-md border bg-muted/60 p-3 font-mono text-sm leading-5 outline-none resize-none"
            aria-label="Mermaid code"
            style={{ minHeight: 260 }}
          />
        </div>
      ) : (
        <div
          className={"bn-visual-media"}
          data-text-align={props.block.props.textAlignment}
        >
          <div
            className="relative inline-block"
            style={{
              width:
                props.block.props.textAlignment === "justify"
                  ? "100%"
                  : width || "auto",
            }}
            ref={previewRef}
          >
            <div ref={mermaidRef} className="overflow-auto" />
            <ResizableHandles onResizeStart={startResize} />
          </div>
        </div>
      )}
    </div>
  );
};

const RenderMermaid: typeof MermaidBlockComponent = MermaidBlockComponent;
export const ReactMermaidBlock = createReactBlockSpec(mermaidBlockConfig, {
  render: RenderMermaid,
});
