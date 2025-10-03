// Normalize backend error shapes into { field, message }
// Supports FastAPI/Pydantic validation errors and our custom { field, message }

export type FieldError = { field: string; message: string };

// FastAPI error format when validation fails (422)
// { detail: [{ type, loc: ['body','name'], msg, input, ctx }] }
function parseFastApiValidation(detail: unknown): FieldError[] {
    if (!Array.isArray(detail)) return [];
    return detail
        .map((entry: any) => {
            const loc = Array.isArray(entry?.loc) ? entry.loc : [];
            const field = typeof loc[1] === 'string' ? loc[1] : undefined;
            const message = typeof entry?.msg === 'string' ? entry.msg : undefined;
            if (!field || !message) return undefined;
            return { field, message } as FieldError;
        })
        .filter(Boolean) as FieldError[];
}

// Our custom error shape { field: 'path', message: '...' }
function parseCustom(detail: unknown): FieldError[] {
    if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
        const d = detail as Record<string, unknown>;
        if (typeof d.field === 'string' && typeof d.message === 'string') {
            return [{ field: d.field, message: d.message }];
        }
    }
    return [];
}

export function extractFieldErrors(error: unknown): FieldError[] {
    // ApiError from lib/api exposes `response` that may contain { detail }
    const maybe = error as { response?: unknown } | undefined;
    const payload = maybe?.response;
    if (!payload || typeof payload !== 'object') return [];

    const obj = payload as Record<string, unknown>;
    const detail = obj.detail ?? payload;

    const fastapi = parseFastApiValidation(detail);
    if (fastapi.length) return fastapi;

    const custom = parseCustom(detail);
    if (custom.length) return custom;

    return [];
}

export function extractFirstMessage(error: unknown): string | undefined {
    const errs = extractFieldErrors(error);
    return errs[0]?.message;
}

