import type { Context } from "hono";
import { getTsJsDriver } from "./driver";
import { mockDriver } from "./mockDriver";
import type {
  InitializeParams,
  ParseFileParams,
  ReadFileParams,
  ReadFolderParams,
  ResolveCallsParams,
} from "./types";

type JsonRpcRequest = {
  jsonrpc?: string;
  method?: string;
  params?: unknown;
  id?: string | number | null;
};

type JsonRpcSuccess = {
  jsonrpc: "2.0";
  result: unknown;
  id: string | number | null;
};

type JsonRpcError = {
  jsonrpc: "2.0";
  error: { code: number; message: string; data?: unknown };
  id: string | number | null;
};

const PARSE_ERROR = -32700;
const INVALID_REQUEST = -32600;
const METHOD_NOT_FOUND = -32601;
const INVALID_PARAMS = -32602;
const INTERNAL_ERROR = -32603;

function err(
  code: number,
  message: string,
  id: string | number | null,
  data?: unknown,
): JsonRpcError {
  return { jsonrpc: "2.0", error: { code, message, data }, id };
}

function ok(result: unknown, id: string | number | null): JsonRpcSuccess {
  return { jsonrpc: "2.0", result, id };
}

function asObject(params: unknown): Record<string, unknown> | null {
  if (params === null || params === undefined) return {};
  if (typeof params === "object" && !Array.isArray(params)) {
    return params as Record<string, unknown>;
  }
  return null;
}

async function dispatch(
  method: string,
  params: unknown,
): Promise<
  | { ok: true; value: unknown }
  | { ok: false; code: number; message: string; data?: unknown }
> {
  const obj = asObject(params);
  if (obj === null) {
    return {
      ok: false,
      code: INVALID_PARAMS,
      message: "Params must be a JSON object",
    };
  }

  try {
    switch (method) {
      case "initialize": {
        const p = obj as unknown as InitializeParams;
        if (typeof p.project_path !== "string") {
          return {
            ok: false,
            code: INVALID_PARAMS,
            message: "project_path is required",
          };
        }
        return { ok: true, value: getTsJsDriver().initialize(p) };
      }
      case "parse_file": {
        const p = obj as unknown as ParseFileParams;
        if (typeof p.file_path !== "string" || typeof p.content !== "string") {
          return {
            ok: false,
            code: INVALID_PARAMS,
            message: "file_path and content are required",
          };
        }
        return { ok: true, value: getTsJsDriver().parseFile(p) };
      }
      case "resolve_calls": {
        const p = obj as unknown as ResolveCallsParams;
        if (typeof p.file_path !== "string" || !Array.isArray(p.calls)) {
          return {
            ok: false,
            code: INVALID_PARAMS,
            message: "file_path and calls[] are required",
          };
        }
        return { ok: true, value: getTsJsDriver().resolveCalls(p) };
      }
      case "read_or_inject_file_id": {
        const p = obj as unknown as ReadFileParams;
        if (typeof p.file_path !== "string") {
          return {
            ok: false,
            code: INVALID_PARAMS,
            message: "file_path is required",
          };
        }
        return { ok: true, value: getTsJsDriver().readOrInjectFileId(p) };
      }
      case "read_or_inject_folder_id": {
        const p = obj as unknown as ReadFolderParams;
        if (typeof p.folder_path !== "string") {
          return {
            ok: false,
            code: INVALID_PARAMS,
            message: "folder_path is required",
          };
        }
        return { ok: true, value: getTsJsDriver().readOrInjectFolderId(p) };
      }
      case "shutdown":
        return { ok: true, value: mockDriver.shutdown(obj) };
      default:
        return {
          ok: false,
          code: METHOD_NOT_FOUND,
          message: `Unknown method: ${method}`,
        };
    }
  } catch (e) {
    const message = e instanceof Error ? e.message : String(e);
    return {
      ok: false,
      code: INTERNAL_ERROR,
      message,
    };
  }
}

export async function handleJsonRpcBody(
  raw: unknown,
): Promise<
  | JsonRpcSuccess
  | JsonRpcError
  | Array<JsonRpcSuccess | JsonRpcError>
> {
  if (Array.isArray(raw)) {
    const out = await Promise.all(raw.map((r) => handleSingle(r)));
    return out;
  }
  return handleSingle(raw);
}

async function handleSingle(
  raw: unknown,
): Promise<JsonRpcSuccess | JsonRpcError> {
  if (raw === null || typeof raw !== "object") {
    return err(INVALID_REQUEST, "Invalid Request", null);
  }

  const req = raw as JsonRpcRequest;
  const id = req.id === undefined ? null : req.id;

  if (req.jsonrpc !== "2.0") {
    return err(INVALID_REQUEST, "jsonrpc must be 2.0", id);
  }
  if (typeof req.method !== "string" || !req.method) {
    return err(INVALID_REQUEST, "method is required", id);
  }

  const result = await dispatch(req.method, req.params);
  if (!result.ok) {
    return err(result.code, result.message, id);
  }
  return ok(result.value, id);
}

export async function jsonRpcPost(c: Context) {
  let body: unknown;
  try {
    body = await c.req.json();
  } catch {
    return c.json(err(PARSE_ERROR, "Parse error", null), 400);
  }

  try {
    const response = await handleJsonRpcBody(body);
    return c.json(response);
  } catch {
    return c.json(err(INTERNAL_ERROR, "Internal error", null), 500);
  }
}
