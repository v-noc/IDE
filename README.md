# V-NOC: Graph Based IDE

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Discord](https://img.shields.io/badge/Discord-Join%20Us-purple.svg)](https://discord.gg/J5nfPHqyBr)

**Software development is a computational problem that we have mistakenly turned into a memory problem.**


V-NOC is a new kind of coding environment. It replaces the archaic file-and-folder system with a logic Graph, moving the burden of "connecting the dots" from the human brain to the computer.
![V-NOC Main View](/assets/v-noc.gif)

---

## 🚩 The Problem: The "Origami" of Software

Programming isn't hard because logic is complex; it’s hard because our tools are disorganized. We spend our lives creating "origami" structures—complex folder hierarchies and design patterns—just to force real-world logic onto a flat file system meant for storage, not thinking.

> [!IMPORTANT]
> **The Mental Model Debt**
> When you open a project, you don't see how the code works; you see where it is stored. Current "AI IDEs" try to fix this with Chat, but that's just hiding trash under the bed. It looks clean until the complexity piles up and blows up in your face because nobody actually understands the "trust me bro" logic the AI generated.

To fix a bug or add a feature today, you are forced to:

*   **Unwrap the Origami:** Dig through layers of facades and folders just to find the actual logic.
*   **Be the Human Glue:** Manually trace function calls, grep logs, and hunt for docs. You are the "linker" because the IDE doesn't actually understand the relationships.
*   **Mental Compiling:** You have to hold a massive map of the project in your head just to change one line.

We spend 10% of our time coding and 90% wrapping and unwrapping structure.

---

## 🧠 The Philosophy: Programming Like Google Maps

Computers were built to simplify things. If a computer can trace an execution path, a human should never have to.

### 1. From Memory Problem to Computational Problem
In math, you don't solve everything at once; you decompose problems into small, verifiable pieces. V-NOC applies this to code. By using a Graph DB (ArangoDB) instead of a file tree, the computer computes the structure for you. You aren't reading a list of files; you are navigating a logic map.

### 2. Canvas over Chat (Stop Reading, Start Seeing)
English is the new programming language, but a chat box is the wrong interface for it. Nobody wants to read a 100-message log to understand what an agent did. In V-NOC, agents live on a Canvas.

Instead of reading a text log, you watch an animated walkthrough of the changes.

It’s like Google Maps for your codebase: You interact with words, but the response is a visual map that anyone can understand.

### 3. Killing the "Side Quest"
In a traditional IDE, every piece of information is a distraction.

*   **Need logs?** You have to scroll through a messy terminal.
*   **Need docs?** You have to switch to a browser.
*   **Need the call stack?** You have to trigger a debugger.

In V-NOC, everything is already there. Logs, documentation, and code are all part of the same node. You only see what is mathematically necessary for the task at hand. No noise, no accidental complexity.

### The Goal
I want to make programming fun and clear again. If you can read a map, you should be able to read code. V-NOC isn't about hiding the details; it's about simplifying the organization so the details actually make sense.

### 4. Flexibility Over Rigidity
Graphs are flexible by nature. V‑NOC lets you view and work on your project based on what you need at the moment—whether that’s a high‑level system overview or a deep dive into a single execution path—without moving or restructuring files.

Even in a large codebase, you can isolate and focus on one feature at a time. This is similar to how hardware is repaired: if the power supply fails, you fix the power supply. You don’t need to understand or load the motherboard, RAM, or every other component. You only interact with what’s relevant.

V‑NOC applies the same principle to software. Dependencies are connected and visible, making it easy to isolate a feature, create a sandbox or playground for it, and run or test it independently—manually or with an agent. No unnecessary context, no side quests, just the parts you need to get the job done.

![Advanced Visualization](/assets/base_class_mro.png)

---

## 🛠️ The Solution: A Living Knowledge Graph

Instead of a file tree, the core of V-NOC is an **interactive, multidimensional map.**

*   **The Code is the Database:** Your project is stored as nodes (functions, classes) and edges (calls, imports, dependencies).
*   **Hierarchical Context:** Logs follow the code's call graph. You see the "why", "where", and "how" in one view.
*   **The AI Superpower:** We give AI agents the structured context they need. They don't guess; they query the graph, making their work easy to audit.

---

## 🔮 Project Vision & Future

The tools used in this project were chosen for speed and simplicity, allowing ideas to be prototyped, tested, and shipped quickly. Much of the system is experimental by design, which requires maximum flexibility and minimal friction during development.

> [!NOTE]
>
> If the project gains enough traction and community support, I plan to migrate critical components—especially the sync pipeline—to **Rust**. That pipeline must be smooth, reliable, and frictionless for developers.

I’ve already optimized the codebase as much as reasonably possible, but Python is unforgiving when it comes to performance mistakes. I’ve identified several performance bottlenecks, including in the call‑chain builder, and will continue investigating and optimizing other parts of the system as well.

### Prerequisites
- **Python** 3.12+ (uv recommended)
- **Node.js** 18+ (Yarn recommended)
- **Docker** (for ArangoDB)

### 1) Backend Setup
```bash
# Create venv and install dependencies
uv venv
make install-backend
```

### 2) Frontend Setup
```bash
make install-frontend
```

### 3) Launch Environment
```bash
make start-db     # Launch ArangoDB in Docker
make dev          # Start both Backend and Frontend
```

> [!TIP]
>
> Use `make help` to see all available commands.



## 🤝 Community & License

V-NOC is built for the community. We are moving away from the "chaos of disorganization" toward automated development.

- **Join the Discord:** [discord.gg/J5nfPHqyBr](https://discord.gg/J5nfPHqyBr)
- **License:** [AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0)

> [!NOTE]
> Commercial/proprietary use requires a separate license. Contact the maintainers for details.

---

**Interested in contributing?** Check our development guide or jump into Discord!
