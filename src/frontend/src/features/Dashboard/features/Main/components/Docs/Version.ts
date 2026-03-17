import { createExtension, type BlockNoteEditor } from "@blocknote/core";
import { Plugin, PluginKey } from "prosemirror-state";
import { Decoration, DecorationSet } from "prosemirror-view";
import { diffWords } from "diff";

interface DiffPluginState {
  oldBlockMap: Map<string, any> | null;
}

const versionDiffKey = new PluginKey<DiffPluginState>("versionDiff");

const BLOCK_ADDED_STYLE = "background: rgba(34, 197, 94, 0.15); border-left: 3px solid #16a34a;";
const BLOCK_MODIFIED_STYLE = "background: rgba(234, 179, 8, 0.1); border-left: 3px solid #ca8a04;";

// ====================== ROBUST HELPERS ======================

function buildBlockMap(json: unknown): Map<string, any> {
  const map = new Map<string, any>();
  if (!json) return map;

  const blocks = Array.isArray(json)
    ? json
    : (json as any)?.content ?? (json as any)?.blocks ?? [];

  function recurse(bs: any[]) {
    for (const block of bs) {
      if (block?.id) map.set(block.id, block);
      if (block?.children?.length) recurse(block.children);
    }
  }
  recurse(blocks);
  return map;
}

// Extract text from BlockNote JSON block (defensive)
function getBlockTextContent(block: any): string {
  if (!block?.content) return "";
  // Handle both array content and string content
  if (Array.isArray(block.content)) {
    return block.content
      .map((c: any) => {
        if (typeof c === "string") return c;
        if (c?.type === "text" && typeof c.text === "string") return c.text;
        return "";
      })
      .join("");
  }
  if (typeof block.content === "string") return block.content;
  return "";
}

// Extract text from ProseMirror node (current editor state)
function getNodeTextContent(node: any): string {
  let text = "";
  node.descendants((n: any) => {
    if (n.isText && n.text) text += n.text;
  });
  return text;
}

// Get text node positions within a block for mapping diff offsets
function getTextNodePositions(
  node: any,
  basePos: number
): Array<{ from: number; to: number; text: string; node: any }> {
  const positions: Array<{ from: number; to: number; text: string; node: any }> = [];

  node.descendants((child: any, pos: number) => {
    if (child.isText && child.text) {
      positions.push({
        from: basePos + pos,
        to: basePos + pos + child.nodeSize,
        text: child.text,
        node: child
      });
    }
  });

  return positions;
}

// Map character offset to document position
function offsetToPosition(
  textNodes: Array<{ from: number; text: string }>,
  offset: number
): number {
  let currentOffset = 0;

  for (const node of textNodes) {
    const nodeLength = node.text.length;
    if (currentOffset + nodeLength > offset) {
      return node.from + (offset - currentOffset);
    }
    currentOffset += nodeLength;
  }

  // Return end of last node
  return textNodes[textNodes.length - 1]?.from + textNodes[textNodes.length - 1]?.text.length || 0;
}

// ====================== WORD-LEVEL DIFF ======================

// ====================== WORD-LEVEL DIFF WITH REMOVALS ======================

function calculateWordDecorations(
  node: any,
  pos: number,
  oldBlock: any
): Decoration[] {
  const decorations: Decoration[] = [];

  const currentText = getNodeTextContent(node);
  const oldText = getBlockTextContent(oldBlock);

  if (currentText === oldText) return decorations;

  const diffs = diffWords(oldText, currentText);
  const textNodes = getTextNodePositions(node, pos + 1);

  if (textNodes.length === 0 && diffs.some(d => d.removed)) {
    // All content removed - show entire old text as removed at block start
    const widget = document.createElement("span");
    widget.textContent = oldText;
    widget.style.cssText = WORD_REMOVED_STYLE;
    widget.className = "diff-removed";

    decorations.push(
      Decoration.widget(pos + 1, () => widget, {
        side: -1,
        key: `removed-all-${pos}`
      })
    );

    decorations.push(
      Decoration.node(pos, pos + node.nodeSize, { style: BLOCK_MODIFIED_STYLE })
    );
    return decorations;
  }

  let newOffset = 0;

  for (const part of diffs) {
    const length = part.value.length;

    if (part.added) {
      // Green highlight on existing text
      const from = offsetToPosition(textNodes, newOffset);
      const to = offsetToPosition(textNodes, newOffset + length);

      if (from < to) {
        decorations.push(
          Decoration.inline(from, to, { style: WORD_ADDED_STYLE }, { inclusiveEnd: false })
        );
      }
      newOffset += length;

    } else if (part.removed) {
      // Red strikethrough - insert as widget since text doesn't exist in current doc
      const insertPos = offsetToPosition(textNodes, newOffset);

      const widget = document.createElement("span");
      widget.textContent = part.value;
      widget.style.cssText = WORD_REMOVED_STYLE;
      widget.className = "diff-removed";
      widget.setAttribute("data-removed-text", "true");

      decorations.push(
        Decoration.widget(insertPos, () => widget, {
          side: -1,  // Place before content at this position
          key: `removed-${insertPos}-${part.value}-${length}`
        })
      );
      // Don't advance newOffset - removed text isn't in current document

    } else {
      // Unchanged - just advance offset
      newOffset += length;
    }
  }

  // Background for modified block
  decorations.push(
    Decoration.node(pos, pos + node.nodeSize, { style: BLOCK_MODIFIED_STYLE })
  );

  return decorations;
}

// Update styles to be more visible
const WORD_ADDED_STYLE = "background: rgba(34, 197, 94, 0.4); border-radius: 2px; padding: 0 2px; margin: 0 1px;";
const WORD_REMOVED_STYLE = "background: rgba(239, 68, 68, 0.3); text-decoration: line-through; color: #991b1b; border-radius: 2px; padding: 0 2px; margin: 0 1px; font-style: italic;";
// ====================== EXTENSION ======================

export const VersionDiffExtension = createExtension(({ editor }) => {
  const plugin = new Plugin({
    key: versionDiffKey,
    state: {
      init() {
        return { oldBlockMap: null, oldJson: null };
      },
      apply(tr, prev) {
        const meta = tr.getMeta(versionDiffKey);
        if (meta) {
          return {
            oldBlockMap: meta.oldJson ? buildBlockMap(meta.oldJson) : null,
            oldJson: meta.oldJson || null,
          };
        }
        return prev;
      },
    },
    props: {
      decorations(state) {
        const pluginState = versionDiffKey.getState(state);
        if (!pluginState?.oldBlockMap) return null;

        const oldBlockMap = pluginState.oldBlockMap;
        const decorations: Decoration[] = [];

        state.doc.descendants((node, pos) => {
          if (node.type.name !== "blockContainer" || !node.attrs?.id) return true;

          const id = node.attrs.id;
          const oldBlock = oldBlockMap.get(id);

          if (!oldBlock) {
            // New block - highlight entire block
            decorations.push(
              Decoration.node(pos, pos + node.nodeSize, { style: BLOCK_ADDED_STYLE })
            );
            return false; // Don't process children, whole block is new
          }

          // Block exists in both versions - check for word-level changes
          const wordDecorations = calculateWordDecorations(node, pos, oldBlock);
          decorations.push(...wordDecorations);

          return true; // Continue into children
        });

        return decorations.length > 0
          ? DecorationSet.create(state.doc, decorations)
          : null;
      },
    },
  });

  // Helper to dispatch transactions (fixes the transact error)
  const dispatchMeta = (oldJson: unknown | null) => {
    // Access the ProseMirror view through BlockNote's editor
    const pmView = (editor as any).prosemirrorView ||
      (editor as any)._tiptapEditor?.view ||
      (editor as any).view;

    if (pmView?.dispatch) {
      const tr = pmView.state.tr.setMeta(versionDiffKey, { oldJson });
      pmView.dispatch(tr);
      return true;
    }
    return false;
  };

  return {
    key: "versionDiff",
    prosemirrorPlugins: [plugin],

    showDiff: (oldJson: unknown) => {
      dispatchMeta(oldJson);
    },

    clearDiff: () => {
      dispatchMeta(null);
    },

    // Optional: helper to get current diff state
    isDiffActive: () => {
      const pmView = (editor as any).prosemirrorView ||
        (editor as any)._tiptapEditor?.view;
      if (!pmView) return false;
      const state = versionDiffKey.getState(pmView.state);
      return state?.oldBlockMap !== null;
    }
  };
});
