import { useState, useEffect } from "react";

const CACHE_KEY = "github-stars-v-noc-ide";
const CACHE_DURATION = 1000 * 60 * 60; // 1 hour

interface GitHubRepoResponse {
    stargazers_count: number;
}

export function useGitHubStars() {
    const [stars, setStars] = useState<number | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    useEffect(() => {
        async function fetchStars() {
            try {
                // Check cache first
                const cachedContent = sessionStorage.getItem(CACHE_KEY);
                if (cachedContent) {
                    const { count, timestamp } = JSON.parse(cachedContent);
                    if (Date.now() - timestamp < CACHE_DURATION) {
                        setStars(count);
                        setLoading(false);
                        return;
                    }
                }

                const response = await fetch("https://api.github.com/repos/v-noc/IDE");
                if (!response.ok) {
                    throw new Error("Failed to fetch stars");
                }
                const data: GitHubRepoResponse = await response.json();
                const count = data.stargazers_count;

                setStars(count);
                sessionStorage.setItem(
                    CACHE_KEY,
                    JSON.stringify({ count, timestamp: Date.now() })
                );
            } catch (err) {
                console.error("Error fetching GitHub stars:", err);
                setError(err instanceof Error ? err : new Error("Unknown error"));
            } finally {
                setLoading(false);
            }
        }

        fetchStars();
    }, []);

    return { stars, loading, error };
}
