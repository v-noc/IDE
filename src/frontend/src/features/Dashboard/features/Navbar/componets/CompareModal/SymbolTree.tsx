import type { SymbolChangeNode } from "./SampleData";
import ChangeBadge from "./ChangeBadge";
import { TreeNode } from "@/features/Dashboard/features/Sidebar/components/TreeNode";
import type { AnyNodeTree } from "@/types/project";

// Buttons moved to modal footer; keep only badges in the tree

export const SymbolTree = ({ nodes }: { nodes: SymbolChangeNode[] }) => {
  return (
    <ul className="space-y-1">
      {nodes.map((n) => {
        const nodeLike: AnyNodeTree = {
          _key: n.id,
          _id: n.id,
          created_at: "",
          updated_at: "",
          name: n.name,
          description: "",
          node_type: "file",
          // file tree requires a path; use synthetic
          path: n.id,
          children: (n.children || []).map((c) => ({
            _key: c.id,
            _id: c.id,
            created_at: "",
            updated_at: "",
            name: c.name,
            description: "",
            node_type: c.nodeType === "class" ? "class" : "function",
            // minimal child compatibility
            children: (c.children || []).map((gc) => ({
              _key: gc.id,
              _id: gc.id,
              created_at: "",
              updated_at: "",
              name: gc.name,
              description: "",
              node_type: gc.nodeType === "class" ? "class" : "function",
              children: [],
              position: {
                line_no: 0,
                col_offset: 0,
                end_line_no: 0,
                end_col_offset: 0,
              },
            })),
            position: {
              line_no: 0,
              col_offset: 0,
              end_line_no: 0,
              end_col_offset: 0,
            },
          })),
        } as unknown as AnyNodeTree;

        return (
          <TreeNode
            key={n.id}
            node={nodeLike}
            rightAdornment={<ChangeBadge type={n.changeType} />}
          />
        );
      })}
    </ul>
  );
};

export default SymbolTree;
