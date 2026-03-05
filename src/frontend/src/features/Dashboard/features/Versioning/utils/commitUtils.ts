import type { Commit } from "@/services/versioning";
import type { CommitDisplay } from "../store/useVersioningStore";

function getInitials(author: string): string {
  if (!author?.trim()) return "??";
  const parts = author.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return author.slice(0, 2).toUpperCase();
}

function formatTimestamp(isoTimestamp: string): string {
  try {
    const date = new Date(isoTimestamp);
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    const year = date.getFullYear();
    let hours = date.getHours();
    const minutes = date.getMinutes();
    const ampm = hours >= 12 ? "PM" : "AM";
    hours = hours % 12 || 12;
    const mins = String(minutes).padStart(2, "0");
    return `${month}/${day}/${year} ${hours}:${mins} ${ampm}`;
  } catch {
    return isoTimestamp;
  }
}

export function mapCommitToDisplay(commit: Commit): CommitDisplay {
  return {
    id: commit.id,
    author: commit.author || "Unknown",
    initials: getInitials(commit.author),
    timestamp: formatTimestamp(commit.timestamp),
    message: commit.message || "(no message)",
  };
}
