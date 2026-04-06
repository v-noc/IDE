/** Stubs for RPC methods not implemented in the TS/JS driver yet. */
export const mockDriver = {
  shutdown(_params: Record<string, unknown> | null | undefined) {
    void _params;
    return { status: "ok" as const };
  },
};
