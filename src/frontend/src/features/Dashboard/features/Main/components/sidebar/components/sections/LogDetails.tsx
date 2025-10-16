import React from "react";

export type LogDetailsData = {
  id: string;
  timestamp: string;
  duration_ms: number | null;
  chain_id: string | null;
  payload: { [key: string]: unknown } | null;
  result: unknown | null;
  error: { [key: string]: unknown } | null;
};

type LogDetailsProps = {
  details: LogDetailsData;
};

const LogDetails: React.FC<LogDetailsProps> = ({ details }) => {
  const formatSignificant = (value: number): string => {
    return new Intl.NumberFormat(undefined, {
      maximumSignificantDigits: 3,
      minimumSignificantDigits: 1,
    }).format(value);
  };

  const formatDurationShort = (durationMs: number | null): string => {
    if (durationMs === null || Number.isNaN(durationMs)) return "-";
    const absMs = Math.abs(durationMs);
    if (absMs >= 1000) {
      const seconds = durationMs / 1000;
      return `${formatSignificant(seconds)} s`;
    }
    if (absMs >= 1) {
      return `${formatSignificant(durationMs)} ms`;
    }
    if (absMs === 0) {
      return "0 ms";
    }
    const ns = durationMs * 1_000_000;
    return `${formatSignificant(ns)} ns`;
  };

  return (
    <div className="px-2 py-2">
      <div className="text-xs font-semibold tracking-wide text-muted-foreground">
        Details
      </div>
      <div className="mt-2 grid gap-2 sm:grid-cols-2">
        <div className="text-xs">
          <span className="opacity-70">ID:</span>
          <span className="ml-2 font-mono break-all">{details.id}</span>
        </div>
        <div className="text-xs">
          <span className="opacity-70">Duration:</span>
          <span className="ml-2">
            {formatDurationShort(details.duration_ms)}
          </span>
        </div>
        <div className="text-xs">
          <span className="opacity-70">Timestamp:</span>
          <span className="ml-2">
            {new Date(details.timestamp).toLocaleString()}
          </span>
        </div>
        {details.chain_id && (
          <div className="text-xs">
            <span className="opacity-70">Chain ID:</span>
            <span
              className="ml-2 font-mono truncate max-w-[220px] inline-block align-bottom"
              title={details.chain_id}
            >
              {details.chain_id}
            </span>
          </div>
        )}
      </div>

      {details.error && (
        <div className="mt-3">
          <div className="text-xs font-medium text-red-600">Error</div>
          <pre className="mt-1 max-h-40 overflow-auto rounded bg-red-50 p-2 text-[11px] leading-snug text-red-800">
            {JSON.stringify(details.error, null, 2)}
          </pre>
        </div>
      )}

      {details.payload && (
        <div className="mt-3">
          <div className="text-xs font-medium">Payload</div>
          <pre className="mt-1 max-h-40 overflow-auto rounded bg-muted p-2 text-[11px] leading-snug">
            {JSON.stringify(details.payload, null, 2)}
          </pre>
        </div>
      )}

      {details.result !== null && details.result !== undefined && (
        <div className="mt-3">
          <div className="text-xs font-medium">Result</div>
          <pre className="mt-1 max-h-40 overflow-auto rounded bg-muted p-2 text-[11px] leading-snug">
            {JSON.stringify(details.result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export default LogDetails;
