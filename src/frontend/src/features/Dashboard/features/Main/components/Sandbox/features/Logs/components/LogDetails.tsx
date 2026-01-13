import React from "react";

export interface LogDetailsData {
    created_at: string;
    chain_id: string | null;
    level_name: string | null;
    payload: { [key: string]: unknown } | null;
    result: unknown | null;
    error: { [key: string]: unknown } | null;
}

interface LogDetailsProps {
    details: LogDetailsData;
}

/**
 * Pure presenter for rendering individual log details.
 */
export const LogDetails: React.FC<LogDetailsProps> = ({ details }) => {
    return (
        <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase">
                        Created At
                    </p>
                    <p className="text-xs font-mono">{details.created_at}</p>
                </div>
                <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase">
                        Chain ID
                    </p>
                    <p
                        className="text-xs font-mono truncate max-w-[360px]"
                        title={details.chain_id ?? undefined}
                    >
                        {details.chain_id || "-"}
                    </p>
                </div>
            </div>

            {details.payload && Object.keys(details.payload).length > 0 && (
                <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase mb-2">
                        Payload
                    </p>
                    <pre className="bg-background border border-border rounded p-2 text-xs overflow-auto max-h-40">
                        {JSON.stringify(details.payload, null, 2)}
                    </pre>
                </div>
            )}

            {details.result !== null && details.result !== undefined && (
                <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase mb-2">
                        Result
                    </p>
                    <pre className="bg-background border border-border rounded p-2 text-xs overflow-auto max-h-40">
                        {JSON.stringify(details.result, null, 2)}
                    </pre>
                </div>
            )}

            {details.error && (
                <div>
                    <p className="text-xs font-semibold text-muted-foreground uppercase mb-2">
                        Error
                    </p>
                    <pre className="bg-destructive/10 border border-destructive/30 rounded p-2 text-xs overflow-auto max-h-40 text-destructive">
                        {JSON.stringify(details.error, null, 2)}
                    </pre>
                </div>
            )}
        </div>
    );
};
