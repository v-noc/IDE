# V-NOC: The Post-File Era

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Discord](https://img.shields.io/badge/Discord-Join%20Us-purple.svg)](https://discord.gg/J5nfPHqyBr)

**Software development is a computational problem that we have mistakenly turned into a memory problem.**


V-NOC is a reimagining of the coding environment. It replaces the archaic file-and-folder system with a **Native Knowledge Graph**, moving the burden of "connecting the dots" from the human brain to the computer.
![V-NOC Main View](/assets/v-noc.gif)

---

## 🚩 The Problem: The "Origami" of Software

Programming isn't hard because logic is complex; it’s hard because our tools are disorganized. We have spent decades creating "origami" structures—complex folder hierarchies and design patterns—just to model real-world logic onto a flat file system.

> [!IMPORTANT]
> **The Mental Model Debt**
> When you open a project, you don't see how the code works; you see where it is stored.

To fix a bug or add a feature, you currently have to:
1. **Unwrap the Origami:** Dig through layers of facades, abstractions, and folder structures to find the logic.
2. **The Human-in-the-Loop:** Act as the "glue," manually tracing function calls, grepping logs, and hunting for documentation.
3. **Memory Overload:** Hold a massive "map" of the project in your head just to make a one-line change.

This "facade layer" is why it's nearly impossible to estimate task time. We spend 10% coding and 90% **wrapping and unwrapping** structure.

---

## 🧠 The Philosophy: Programming Should Be Easy

We believe that **computers were built to simplify things.** If a computer can trace an execution path, a human should never have to.

### 1. From Thinking Problem to Computational Problem
Most coding tasks—finding dependencies, tracing data flow, or locating relevant logs—are repetitive, mechanical tasks. V-NOC allocates these to the computer. By treating code as a graph, the computer knows exactly what is connected. The human is no longer the "linker."

### 2. Eliminating the "Side Quest"
In a traditional IDE, every piece of information is a "side quest."
- Need logs? *Open the terminal.*
- Need docs? *Open the browser.*
- Need the call stack? *Start debugging.*

In V-NOC, **everything is already there.** Logs, documentation, and code are all part of the same node in ArangoDB.

### 3. Flexibility Over Rigidity
Knowledge graphs are flexible. V-NOC allows you to view your project based on your current needs—high-level architecture or deep-dive execution traces—without ever moving a file.

![Advanced Visualization](/assets/base_class_mro.png)

---

## 🛠️ The Solution: A Living Knowledge Graph

Instead of a file tree, the core of V-NOC is an **interactive, multidimensional map.**

- **The Code is the Database:** Your project is stored as nodes (functions, classes, variables) and edges (calls, imports, dependencies).
- **Hierarchical Context:** Logs follow the code's call graph. You see the "why" and the "how" in one view.
- **The AI Superpower:** We give AI agents the structured context they need. They don't guess; they query the graph.

| Feature | Legacy IDE | V-NOC |
| :--- | :--- | :--- |
| **Storage** | Flat File System | ArangoDB Graph |
| **Navigation** | Folders & Grep | Call Graph Traversal |
| **Context** | Manual Linking | Automated Attribution |
| **AI** | Text-based RAG | Graph-native Context |

---

## 🚀 Quick Start

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
> Use `make help` to see all available commands.



## 🤝 Community & License

V-NOC is built for the community. We are moving away from the "chaos of disorganization" toward automated development.

- **Join the Discord:** [discord.gg/J5nfPHqyBr](https://discord.gg/J5nfPHqyBr)
- **License:** [AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0)

> [!NOTE]
> Commercial/proprietary use requires a separate license. Contact the maintainers for details.

---

**Interested in contributing?** Check our development guide or jump into Discord!