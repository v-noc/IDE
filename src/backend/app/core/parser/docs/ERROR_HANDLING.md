# Error Handling and Reporting Strategy

This document outlines a comprehensive strategy for handling errors, logging issues, and reporting the status of the parsing process. A robust parser must be resilient to common problems like syntax errors, unresolved symbols, and unexpected code structures.

## Core Principles

1.  **Fail Gracefully, Not Silently:** The parser should never crash due to an error in the user's code. It should catch the error, log it, and continue parsing other files or components.
2.  **Collect, Don't Abort:** The goal is to complete the analysis and provide the user with a list of all issues found, rather than aborting on the first error.
3.  **Structured Reporting:** Errors and warnings should be collected into a structured report that can be easily consumed by an API or displayed in a UI.

## 1. The `AnalysisReport` Object

The `ProjectScanner` will be responsible for creating and managing a single `AnalysisReport` object for each parsing job. This object will be returned to the caller along with the parsed data.

**Proposed `AnalysisReport` Model (`models/reports.py`):**
```python
class AnalysisIssue(BaseModel):
    severity: Literal["error", "warning"]
    file_path: str | None
    line_no: int | None
    message: str
    category: Literal[
        "SyntaxError",
        "UnresolvedImport",
        "UnresolvedCallTarget",
        "ParserInternalError"
    ]

class AnalysisReport(BaseModel):
    status: Literal["completed", "completed_with_issues", "failed"]
    issues: list[AnalysisIssue] = []
    duration_seconds: float
    files_analyzed: int
```

## 2. Error Handling at Each Stage

### Stage 1: File Parsing (`PythonFileParser`)
-   **Problem:** A file contains invalid Python syntax (`SyntaxError`).
-   **Handling:**
    -   The `PythonFileParser` will wrap its `ast.parse()` call in a `try...except SyntaxError as e:` block.
    -   If an exception is caught, it will create an `AnalysisIssue` with:
        -   `severity`: "error"
        -   `file_path`: The path of the broken file.
        -   `line_no`: `e.lineno`
        -   `message`: `e.msg`
        -   `category`: "SyntaxError"
    -   It will add this issue to the `AnalysisReport`.
    -   It will then **stop processing that specific file** and move on to the next one.

### Stage 2: Symbol Resolution (`SymbolTable`)
-   **Problem:** The `SymbolTable` cannot resolve an import or a call target.
-   **Handling:**
    -   The `resolve_*` methods in the `SymbolTable` will **not** raise exceptions. Instead, they will return `None`.
    -   The calling visitor (e.g., `DependencyVisitor`, `CallVisitor`) is responsible for checking if the result is `None`.
    -   If the result is `None`, the visitor will create an `AnalysisIssue` with:
        -   `severity`: "warning" (as this is often not a fatal error)
        -   `file_path`: The path of the current file.
        -   `line_no`: The line number of the unresolved import or call.
        -   `message`: "Could not resolve import 'foo.bar'" or "Could not resolve call target 'my_var.do_thing()'".
        -   `category`: "UnresolvedImport" or "UnresolvedCallTarget"
    -   This issue is added to the report, and the visitor continues its traversal. No broken edge is created in the graph.

### Stage 3: Internal Parser Errors
-   **Problem:** An unexpected error occurs within our own parser logic (a `KeyError`, `AttributeError`, etc.).
-   **Handling:**
    -   The main `ProjectScanner.scan()` method will be wrapped in a top-level `try...except Exception as e:` block.
    -   If any unexpected exception bubbles up, it will be caught here.
    -   This will create a single, fatal `AnalysisIssue`:
        -   `severity`: "error"
        -   `message`: A formatted traceback of the internal error.
        -   `category`: "ParserInternalError"
    -   The `AnalysisReport.status` will be set to `"failed"`.
    -   The analysis process will be aborted, and the report will be returned immediately. This indicates a bug in our parser, not the user's code.

## 3. Final Output

The API endpoint that triggers the scan will no longer just return a success message. It will return the `AnalysisReport` object, serialized as JSON. A UI can then use this report to display a summary of the analysis and a detailed list of any issues found, allowing the user to easily navigate to and fix the problematic code.
