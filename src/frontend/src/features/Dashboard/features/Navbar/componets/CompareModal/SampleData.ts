export type ChangeType = "added" | "removed" | "modified";

export interface FileChange {
    path: string;
    changeType: ChangeType;
    additions: number;
    deletions: number;
}

export interface SymbolChangeNode {
    id: string;
    name: string;
    nodeType: "class" | "function" | "file";
    changeType: ChangeType;
    children?: SymbolChangeNode[];
}

export interface BranchComparisonData {
    base: string;
    compare: string;
    summary: {
        filesChanged: number;
        additions: number;
        deletions: number;
        addedFiles: number;
        removedFiles: number;
    };
    files: FileChange[];
    symbols: SymbolChangeNode[];
    diffs: Record<string, string>; // path -> unified diff string (sample)
}

export const SAMPLE_DATA: BranchComparisonData = {
    base: "main",
    compare: "feature/refactor-parser",
    summary: {
        filesChanged: 5,
        additions: 132,
        deletions: 48,
        addedFiles: 2,
        removedFiles: 1,
    },
    files: [
        { path: "src/parser/graph_builder.py", changeType: "modified", additions: 6, deletions: 2 },
        { path: "src/parser/analyzer.py", changeType: "modified", additions: 28, deletions: 8 },
        { path: "src/core/new_feature.py", changeType: "added", additions: 52, deletions: 0 },
        { path: "src/core/legacy.py", changeType: "removed", additions: 0, deletions: 20 },
        { path: "src/ui/tree_view.py", changeType: "modified", additions: 12, deletions: 8 },
    ],
    symbols: [
        {
            id: "file:src/parser/graph_builder.py",
            name: "graph_builder.py",
            nodeType: "file",
            changeType: "modified",
            children: [
                {
                    id: "class:GraphBuilder",
                    name: "class GraphBuilder",
                    nodeType: "class",
                    changeType: "modified",
                    children: [
                        {
                            id: "fn:build",
                            name: "build()",
                            nodeType: "function",
                            changeType: "modified",
                        },
                        {
                            id: "fn:optimize",
                            name: "optimize()",
                            nodeType: "function",
                            changeType: "added",
                        },
                    ],
                },
            ],
        },
        {
            id: "file:src/core/legacy.py",
            name: "legacy.py",
            nodeType: "file",
            changeType: "removed",
            children: [
                {
                    id: "class:Legacy",
                    name: "class Legacy",
                    nodeType: "class",
                    changeType: "removed",
                },
            ],
        },
        {
            id: "file:src/core/new_feature.py",
            name: "new_feature.py",
            nodeType: "file",
            changeType: "added",
            children: [
                {
                    id: "fn:activate",
                    name: "activate()",
                    nodeType: "function",
                    changeType: "added",
                },
            ],
        },
    ],
    diffs: {
        "src/parser/graph_builder.py": `diff --git a/src/parser/graph_builder.py b/src/parser/graph_builder.py
index 1c2d3f..4a5b6c 100644
--- a/src/parser/graph_builder.py
+++ b/src/parser/graph_builder.py
@@ -1,6 +1,16 @@
-class GraphBuilder:
-    def build(self):
-        # old implementation
-        return True
+class GraphBuilder:
+    def __init__(self, optimize: bool = False) -> None:
+        self.optimize = optimize
+
+    def build(self) -> bool:
+        # new optimized build flow
+        if self.optimize:
+            self._run_optimizer()
+        return True
+
+    def _run_optimizer(self) -> None:
+        # added optimization
+        pass
`,
        "src/core/new_feature.py": `diff --git a/src/core/new_feature.py b/src/core/new_feature.py
new file mode 100644
--- /dev/null
+++ b/src/core/new_feature.py
@@ -0,0 +1,8 @@
+def activate(config: dict) -> bool:
+    """Activate new feature."""
+    if not config:
+        return False
+    # initialization logic
+    return True
`,
        "src/core/legacy.py": `diff --git a/src/core/legacy.py b/src/core/legacy.py
deleted file mode 100644
--- a/src/core/legacy.py
+++ /dev/null
@@ -1,6 +0,0 @@
-class Legacy:
-    def run(self):
-        return True
`,
    },
};


