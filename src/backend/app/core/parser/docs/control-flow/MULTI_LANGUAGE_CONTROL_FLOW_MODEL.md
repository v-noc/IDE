### Multi-language Control Flow Model

#### Common model
- Nodes: Entry, Exit, BasicBlock, Decision, LoopHeader, LoopLatch, Try, Catch, Finally
- Edges: normal, back-edge, exception, guard
- Per-function graphs; program CFG is composition of function CFGs + call edges

#### Language mappings
- JavaScript/TypeScript
  - `switch`: Decision with one edge per `case` and `default`; fall-through edges; `break` edges to switch exit
  - `for/while/do-while`: loop headers and back-edges; labeled `break/continue`
  - `try/catch/finally`: exception edges; finally edge merges
  - async/await: treat `await` as suspension point (optional effect graph)
- Rust
  - `match`: Decision with exhaustive arms; guards; irrefutable patterns
  - loops: `loop` (infinite with explicit breaks), `while`, `for`
  - `?` operator: exception-like early-exit edge (Result/Option flow)

#### Pattern matching
- Represent pattern tests as guard predicates on decision edges
- Bindings introduced in arms are edge-scoped symbols

#### Integration with type facts
- Edges can carry refinements (e.g., `match x { Some(v) => v: T }`)
- JS: control-flow based type narrowing (like TS) can be modeled via guard facts

#### Output
- Uniform CFG schema for all languages so downstream passes (e.g., slicing, impact analysis) are shared 