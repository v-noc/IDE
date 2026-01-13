import { useEffect, useState, useCallback } from 'react';

export function useResizeObserver() {
    const [width, setWidth] = useState(0);
    const [height, setHeight] = useState(0);
    const [element, setElement] = useState<HTMLElement | null>(null);

    // Using a callback ref ensures we capture the node when it mounts/unmounts
    // even if it happens conditionally after the initial render.
    const ref = useCallback((node: HTMLElement | null) => {
        setElement(node);
    }, []);

    useEffect(() => {
        if (!element) return;

        const observer = new ResizeObserver((entries) => {
            const entry = entries[0];
            if (entry) {
                // Use contentRect for precise dimensions excluding border/padding if needed,
                // or just standard rect. contentRect is standard for ResizeObserver.
                setWidth(entry.contentRect.width);
                setHeight(entry.contentRect.height);
            }
        });

        observer.observe(element);

        return () => {
            observer.disconnect();
        };
    }, [element]);

    return { ref, width, height };
}
