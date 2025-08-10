### Python Control Flow Analysis Guide

#### Scope
- Build a per-function Control Flow Graph (CFG) with nodes and edges
- Cover: sequence, conditionals, loops (`for`/`while`), `break`/`continue`, `try/except/finally`, `with`, `match` (3.10+), `yield`/`return`

#### CFG nodes
- BasicBlock with list of statements and source span
- Decision nodes (If, Match)
- Loop nodes (For, While) with back-edges
- Exception edges from statements that may raise

#### Loops
- For: init → iter block → body → back-edge → exit
- While: condition → body → back-edge → exit
- Break: edge to loop exit; Continue: edge to loop header
- Comprehensions: treat as implicit loops with inner scopes

#### Match (Python 3.10+)
- Decision node with one outgoing edge per case
- Guards: additional predicate edge
- Exhaustiveness unknown → add default fall-through if no wildcard

#### Exception handling
- Try/Except: edges from try-body to except handlers and to finally
- Finally always executes before exit; model with mandatory edge

#### Dataflow hooks
- Visitors can annotate CFG nodes with TypeFacts
- Optional SSA renaming for advanced analyses

#### Output
- Per-function `ControlFlowGraph` embedded in `DetailResult`

#### Testing
- Golden CFG snapshots for representative constructs 